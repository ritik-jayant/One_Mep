from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import NbcSkill
from app.services.llm import client as llm


SCHEMA = """{
  "occupancy_detected": "string",
  "building_notes": "string",
  "matched_rule_codes": ["NBC-FF-01"],
  "rationale": "string",
  "risks": ["string"]
}"""


def _skills_payload(db: Session, occupancy: str) -> list[dict[str, str]]:
    rows = (
        db.query(NbcSkill)
        .filter(NbcSkill.active == 1)
        .filter((NbcSkill.occupancy == "all") | (NbcSkill.occupancy == occupancy))
        .all()
    )
    return [
        {
            "code": r.code,
            "title": r.title,
            "occupancy": r.occupancy,
            "category": r.category,
            "requirement": r.requirement,
        }
        for r in rows
    ]


def match_rules(db: Session, occupancy: str, drawing_path: str | None) -> dict[str, Any]:
    skills = _skills_payload(db, occupancy)
    result = None
    if llm.available():
        try:
            result = llm.complete_json(
                (
                    f"Occupancy declared by engineer: {occupancy}.\n"
                    "Read the plot diagram if provided. Select every applicable NBC skill from the list. "
                    "Do not drop life-safety or hydrant/sprinkler rules when the occupancy typically needs them.\n"
                    f"NBC skills:\n{json.dumps(skills, indent=2)}"
                ),
                image_path=drawing_path,
                schema_hint=SCHEMA,
            )
        except Exception as exc:
            result = None
            fallback_note = f"LLM call failed ({exc.__class__.__name__}); used occupancy filter."
    if result is None:
        result = {
            "occupancy_detected": occupancy,
            "building_notes": locals().get("fallback_note")
            or "LLM offline — applied occupancy filter plus always-on fire-fighting rules.",
            "matched_rule_codes": [s["code"] for s in skills],
            "rationale": "Deterministic fallback matched all active skills for this occupancy.",
            "risks": [],
        }

    codes = set(result.get("matched_rule_codes") or [])
    matched = [s for s in skills if s["code"] in codes] or skills
    result["skills"] = matched
    return result
