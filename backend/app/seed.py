from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import ApprovedPlan, NbcSkill


def seed_nbc(db: Session) -> int:
    path = Path(__file__).parent / "knowledge" / "nbc_seed.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    added = 0
    for item in items:
        exists = db.query(NbcSkill).filter(NbcSkill.code == item["code"]).first()
        if exists:
            continue
        db.add(NbcSkill(**item))
        added += 1
    if not db.query(ApprovedPlan).first():
        db.add(
            ApprovedPlan(
                name="Reference low-rise residential",
                occupancy="residential",
                summary="Yard hydrants at opposite corners, hose reels at stair, wet riser, 75 kL UGT, electric+jockey pumps, ABC extinguishers on escape route.",
                design_json=json.dumps(
                    {
                        "plot_footprint_m": {"width": 36, "depth": 22},
                        "hydrants": [{"id": "YH-1", "x": 3, "y": 2}, {"id": "YH-2", "x": 33, "y": 20}],
                        "hose_reels": [{"id": "HR-1", "x": 8, "y": 10}],
                        "pumps": [{"id": "FP-1", "x": 2, "y": 2}],
                        "tanks": [{"id": "UGT-1", "x": 0.5, "y": 0.5, "capacity_kl": 75}],
                    }
                ),
            )
        )
        added += 1
    db.commit()
    return added
