from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import ApprovedPlan, DesignIssue, NbcSkill
from app.schemas.project import NbcSkillIn, NbcSkillOut

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/nbc", response_model=list[NbcSkillOut])
def list_nbc(db: Session = Depends(get_db)) -> list[NbcSkill]:
    return db.query(NbcSkill).order_by(NbcSkill.code).all()


@router.post("/nbc", response_model=NbcSkillOut)
def add_nbc(body: NbcSkillIn, db: Session = Depends(get_db)) -> NbcSkill:
    row = NbcSkill(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/issues")
def list_issues(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(DesignIssue).order_by(DesignIssue.id.desc()).limit(100).all()
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "severity": r.severity,
            "issue": r.issue,
            "correction": r.correction,
            "occupancy": r.occupancy,
        }
        for r in rows
    ]


@router.get("/approved")
def list_approved(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(ApprovedPlan).order_by(ApprovedPlan.id.desc()).all()
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "name": r.name,
            "occupancy": r.occupancy,
            "summary": r.summary,
            "dxf_path": r.dxf_path,
        }
        for r in rows
    ]
