from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    occupancy: str = "residential"


class ProjectOut(BaseModel):
    id: int
    name: str
    occupancy: str
    status: str
    drawing_path: str | None
    dxf_path: str | None
    generation_attempt: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConfirmRulesIn(BaseModel):
    approved: bool
    notes: str = ""
    decided_by: str = "engineer"


class ValidateIn(BaseModel):
    change_type: str = Field(pattern="^(none|minor|major)$")
    notes: str = ""


class EventOut(BaseModel):
    id: int
    step: str
    outcome: str
    detail: str | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class NbcSkillIn(BaseModel):
    code: str
    title: str
    occupancy: str = "all"
    category: str
    requirement: str
    source: str = "engineer"


class NbcSkillOut(NbcSkillIn):
    id: int
    active: int

    model_config = {"from_attributes": True}
