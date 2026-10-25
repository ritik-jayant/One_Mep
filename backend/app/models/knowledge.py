from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class NbcSkill(Base):
    """NBC / engineer-authored rules the matcher retrieves."""

    __tablename__ = "nbc_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    occupancy: Mapped[str] = mapped_column(String(80), default="all")
    category: Mapped[str] = mapped_column(String(80))
    requirement: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(120), default="NBC Part 4 (engineer summary)")
    active: Mapped[int] = mapped_column(Integer, default=1)


class DesignIssue(Base):
    """Design store: past minor/major issues so the agent does not repeat them."""

    __tablename__ = "design_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(Integer)
    severity: Mapped[str] = mapped_column(String(20))  # minor | major | eval_failed
    issue: Mapped[str] = mapped_column(Text)
    correction: Mapped[str | None] = mapped_column(Text)
    occupancy: Mapped[str] = mapped_column(String(80), default="all")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ApprovedPlan(Base):
    """Library of pre-approved / final designs used for evaluation and accuracy."""

    __tablename__ = "approved_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    occupancy: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    design_json: Mapped[str | None] = mapped_column(Text)
    dxf_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
