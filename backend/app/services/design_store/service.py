from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import ApprovedPlan, DesignIssue


def past_issues(db: Session, occupancy: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = (
        db.query(DesignIssue)
        .filter((DesignIssue.occupancy == occupancy) | (DesignIssue.occupancy == "all"))
        .order_by(DesignIssue.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {"severity": r.severity, "issue": r.issue, "correction": r.correction, "occupancy": r.occupancy}
        for r in rows
    ]


def record_issue(
    db: Session,
    *,
    project_id: int,
    occupancy: str,
    severity: str,
    issue: str,
    correction: str | None = None,
) -> DesignIssue:
    row = DesignIssue(
        project_id=project_id,
        occupancy=occupancy,
        severity=severity,
        issue=issue,
        correction=correction,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def approved_summaries(db: Session, occupancy: str, limit: int = 8) -> list[dict[str, Any]]:
    rows = (
        db.query(ApprovedPlan)
        .filter((ApprovedPlan.occupancy == occupancy) | (ApprovedPlan.occupancy == "all"))
        .order_by(ApprovedPlan.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "name": r.name,
            "occupancy": r.occupancy,
            "summary": r.summary,
            "design": json.loads(r.design_json) if r.design_json else None,
        }
        for r in rows
    ]


def save_approved(
    db: Session,
    *,
    project_id: int,
    name: str,
    occupancy: str,
    summary: str,
    design_json: str | None,
    dxf_path: str | None,
) -> ApprovedPlan:
    row = ApprovedPlan(
        project_id=project_id,
        name=name,
        occupancy=occupancy,
        summary=summary,
        design_json=design_json,
        dxf_path=dxf_path,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
