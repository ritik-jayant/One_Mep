from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import AgentEvent, Project, RuleConfirmation
from app.services.cad.dxf_generator import generate_dxf
from app.services.design_store import service as store
from app.services.llm import client as llm
from app.services.nbc.matcher import match_rules

DESIGN_SCHEMA = """{
  "plot_footprint_m": {"width": 40, "depth": 24},
  "hydrants": [{"id": "YH-1", "x": 5, "y": 2, "coverage_m": 45}],
  "hose_reels": [{"id": "HR-1", "x": 8, "y": 8}],
  "sprinklers": [{"id": "SP-1", "x": 4, "y": 4}],
  "extinguishers": [{"id": "FE-1", "x": 3, "y": 10, "type": "ABC"}],
  "risers": [{"id": "WR-1", "x": 1, "y": 12, "type": "wet_riser"}],
  "pumps": [{"id": "FP-1", "x": 2, "y": 2, "duty": "electric"}],
  "tanks": [{"id": "UGT-1", "x": 0.5, "y": 0.5, "capacity_kl": 75}],
  "notes": ["string"],
  "compliance_summary": "string"
}"""

EVAL_SCHEMA = """{
  "pass": true,
  "score": 0.0,
  "failures": ["string"],
  "improvements": ["string"]
}"""


def log(db: Session, project: Project, step: str, outcome: str, detail: Any) -> None:
    text = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)
    db.add(AgentEvent(project_id=project.id, step=step, outcome=outcome, detail=text))
    db.commit()


def match_nbc(db: Session, project: Project) -> dict[str, Any]:
    result = match_rules(db, project.occupancy, project.drawing_path)
    project.matched_rules_json = json.dumps(result)
    project.status = "rules_matched"
    db.commit()
    log(db, project, "match_nbc", "ok", result)
    return result


def confirm_rules(db: Session, project: Project, approved: bool, notes: str, decided_by: str) -> Project:
    db.add(
        RuleConfirmation(
            project_id=project.id,
            approved=1 if approved else 0,
            notes=notes,
            decided_by=decided_by,
        )
    )
    if approved:
        project.status = "rules_confirmed"
        log(db, project, "engineer_confirm_rules", "confirmed", notes or "confirmed")
        db.commit()
        return check_store_and_generate(db, project)

    project.status = "rules_denied"
    log(db, project, "engineer_confirm_rules", "denied", notes or "denied — re-check")
    db.commit()
    return project


def recheck_nbc(db: Session, project: Project) -> dict[str, Any]:
    """Denied path: re-run NBC matching."""
    return match_nbc(db, project)


def check_store_and_generate(db: Session, project: Project) -> Project:
    issues = store.past_issues(db, project.occupancy)
    log(db, project, "check_design_store", "ok", {"count": len(issues), "issues": issues})
    project.status = "store_checked"
    db.commit()
    return generate_and_eval(db, project, issues)


def _fallback_design(project: Project) -> dict[str, Any]:
    return {
        "plot_footprint_m": {"width": 40, "depth": 24},
        "hydrants": [
            {"id": "YH-1", "x": 4, "y": 2, "coverage_m": 45},
            {"id": "YH-2", "x": 36, "y": 22, "coverage_m": 45},
        ],
        "hose_reels": [{"id": "HR-1", "x": 10, "y": 8}, {"id": "HR-2", "x": 28, "y": 16}],
        "sprinklers": [
            {"id": f"SP-{i+1}", "x": 4 + (i % 6) * 6, "y": 4 + (i // 6) * 6} for i in range(12)
        ],
        "extinguishers": [{"id": "FE-1", "x": 6, "y": 10, "type": "ABC"}],
        "risers": [{"id": "WR-1", "x": 2, "y": 12, "type": "wet_riser"}],
        "pumps": [{"id": "FP-1", "x": 2, "y": 2, "duty": "electric"}],
        "tanks": [{"id": "UGT-1", "x": 0.5, "y": 0.5, "capacity_kl": 75}],
        "notes": [
            f"Fallback layout for {project.occupancy} occupancy.",
            "Set LLM_API_KEY for vision-based plot reading and tighter NBC matching.",
        ],
        "compliance_summary": "Deterministic NBC-oriented starter layout.",
    }


def _generate_design(project: Project, issues: list[dict[str, Any]], approved: list[dict[str, Any]]) -> dict[str, Any]:
    if llm.available():
        try:
            rules = json.loads(project.matched_rules_json or "{}")
            return llm.complete_json(
                (
                    f"Generate a fire-fighting layout for occupancy={project.occupancy}.\n"
                    "Use meters, origin at plot SW corner. Place hydrants, hose reels, sprinklers, "
                    "extinguishers, risers, fire pumps and underground tank so coverage is conservative.\n"
                    f"Matched NBC skills:\n{json.dumps(rules.get('skills', []), indent=2)}\n"
                    f"Past issues to AVOID repeating:\n{json.dumps(issues, indent=2)}\n"
                    f"Approved plan patterns to imitate:\n{json.dumps(approved, indent=2)}"
                ),
                image_path=project.drawing_path,
                schema_hint=DESIGN_SCHEMA,
            )
        except Exception:
            pass
    return _fallback_design(project)


def _evaluate(project: Project, design: dict[str, Any], approved: list[dict[str, Any]]) -> dict[str, Any]:
    if llm.available():
        try:
            return llm.complete_json(
                (
                    "Evaluate this fire-fighting design against NBC practice and the approved-plan library. "
                    "Fail if hydrant coverage, tank/pump provision, or riser strategy is missing or unsafe.\n"
                    f"Occupancy: {project.occupancy}\n"
                    f"Design:\n{json.dumps(design, indent=2)}\n"
                    f"Approved plans:\n{json.dumps(approved, indent=2)}"
                ),
                schema_hint=EVAL_SCHEMA,
            )
        except Exception:
            pass
    hydrants = design.get("hydrants") or []
    tanks = design.get("tanks") or []
    pumps = design.get("pumps") or []
    failures = []
    if len(hydrants) < 1:
        failures.append("No yard hydrant placed.")
    if not tanks:
        failures.append("No fire water tank.")
    if not pumps:
        failures.append("No fire pump.")
    return {
        "pass": not failures,
        "score": 0.9 if not failures else 0.3,
        "failures": failures,
        "improvements": ["Confirm hydrant coverage against 45 m hose length."],
    }


def generate_and_eval(db: Session, project: Project, issues: list[dict[str, Any]] | None = None) -> Project:
    issues = issues if issues is not None else store.past_issues(db, project.occupancy)
    approved = store.approved_summaries(db, project.occupancy)
    project.generation_attempt += 1

    design = _generate_design(project, issues, approved)
    project.design_json = json.dumps(design)
    project.status = "design_generated"
    db.commit()
    log(db, project, "generate_design", "ok", design)

    evaluation = _evaluate(project, design, approved)
    project.eval_json = json.dumps(evaluation)
    db.commit()

    if not evaluation.get("pass", False):
        failures = evaluation.get("failures") or ["eval failed"]
        store.record_issue(
            db,
            project_id=project.id,
            occupancy=project.occupancy,
            severity="eval_failed",
            issue="; ".join(failures),
            correction="; ".join(evaluation.get("improvements") or []),
        )
        project.status = "eval_failed"
        log(db, project, "eval_approved_plans", "failed", evaluation)
        db.commit()
        if project.generation_attempt < 3:
            return generate_and_eval(db, project)
        return project

    log(db, project, "eval_approved_plans", "pass", evaluation)
    path = generate_dxf(project.id, design)
    project.dxf_path = str(path)
    project.status = "cad_ready"
    db.commit()
    log(db, project, "generate_cad", "ok", {"dxf_path": project.dxf_path})
    return project


def retry_after_eval_fail(db: Session, project: Project) -> Project:
    return generate_and_eval(db, project)


def engineer_validate(db: Session, project: Project, change_type: str, notes: str) -> Project:
    if change_type == "major":
        store.record_issue(
            db,
            project_id=project.id,
            occupancy=project.occupancy,
            severity="major",
            issue=notes or "Engineer requested major redesign",
            correction=notes,
        )
        project.status = "major_change"
        log(db, project, "engineer_validate", "major_change", notes)
        db.commit()
        return generate_and_eval(db, project)

    if change_type == "minor":
        store.record_issue(
            db,
            project_id=project.id,
            occupancy=project.occupancy,
            severity="minor",
            issue=notes or "Minor engineer adjustment",
            correction=notes,
        )
        log(db, project, "engineer_validate", "minor_change", notes)

    project.status = "approved"
    db.commit()
    log(db, project, "final_design", "approved", notes or "released to client")
    store.save_approved(
        db,
        project_id=project.id,
        name=project.name,
        occupancy=project.occupancy,
        summary=notes or (json.loads(project.design_json or "{}").get("compliance_summary") or "Approved"),
        design_json=project.design_json,
        dxf_path=project.dxf_path,
    )
    log(db, project, "approved_library", "saved", "Approved design saved to library")
    return project
