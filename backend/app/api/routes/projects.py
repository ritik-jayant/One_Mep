from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.models import Project
from app.schemas.project import ConfirmRulesIn, EventOut, ProjectCreate, ProjectOut, ValidateIn
from app.services.agent import pipeline

router = APIRouter(prefix="/projects", tags=["projects"])


def _project(db: Session, project_id: int) -> Project:
    row = db.query(Project).filter(Project.id == project_id).first()
    if not row:
        raise HTTPException(404, "Project not found")
    return row


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.id.desc()).all()


@router.post("", response_model=ProjectOut)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    row = Project(name=body.name, occupancy=body.occupancy, status="created")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)) -> dict:
    row = _project(db, project_id)
    return {
        "id": row.id,
        "name": row.name,
        "occupancy": row.occupancy,
        "status": row.status,
        "drawing_path": row.drawing_path,
        "dxf_path": row.dxf_path,
        "generation_attempt": row.generation_attempt,
        "matched_rules": json.loads(row.matched_rules_json) if row.matched_rules_json else None,
        "design": json.loads(row.design_json) if row.design_json else None,
        "evaluation": json.loads(row.eval_json) if row.eval_json else None,
        "events": [
            EventOut.model_validate(e).model_dump()
            for e in sorted(row.events, key=lambda x: x.id)
        ],
    }


@router.post("/{project_id}/upload", response_model=ProjectOut)
async def upload_drawing(
    project_id: int,
    occupancy: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Project:
    row = _project(db, project_id)
    suffix = Path(file.filename or "plot.png").suffix or ".png"
    dest = settings.upload_dir / f"project_{row.id}{suffix}"
    dest.write_bytes(await file.read())
    row.drawing_path = str(dest)
    row.status = "uploaded"
    if occupancy:
        row.occupancy = occupancy
    db.commit()
    pipeline.log(db, row, "upload", "ok", {"path": row.drawing_path})
    pipeline.match_nbc(db, row)
    db.refresh(row)
    return row


@router.post("/{project_id}/confirm-rules", response_model=ProjectOut)
def confirm_rules(project_id: int, body: ConfirmRulesIn, db: Session = Depends(get_db)) -> Project:
    row = _project(db, project_id)
    pipeline.confirm_rules(db, row, body.approved, body.notes, body.decided_by)
    db.refresh(row)
    return row


@router.post("/{project_id}/recheck-nbc", response_model=ProjectOut)
def recheck_nbc(project_id: int, db: Session = Depends(get_db)) -> Project:
    row = _project(db, project_id)
    pipeline.recheck_nbc(db, row)
    db.refresh(row)
    return row


@router.post("/{project_id}/retry-generate", response_model=ProjectOut)
def retry_generate(project_id: int, db: Session = Depends(get_db)) -> Project:
    row = _project(db, project_id)
    pipeline.retry_after_eval_fail(db, row)
    db.refresh(row)
    return row


@router.post("/{project_id}/validate", response_model=ProjectOut)
def validate(project_id: int, body: ValidateIn, db: Session = Depends(get_db)) -> Project:
    row = _project(db, project_id)
    pipeline.engineer_validate(db, row, body.change_type, body.notes)
    db.refresh(row)
    return row


@router.get("/{project_id}/dxf")
def download_dxf(project_id: int, db: Session = Depends(get_db)) -> FileResponse:
    row = _project(db, project_id)
    if not row.dxf_path or not Path(row.dxf_path).exists():
        raise HTTPException(404, "DXF not generated yet")
    return FileResponse(row.dxf_path, filename=Path(row.dxf_path).name, media_type="application/dxf")
