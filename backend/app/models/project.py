from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    occupancy: Mapped[str] = mapped_column(String(80), default="residential")
    status: Mapped[str] = mapped_column(String(40), default="uploaded")
    drawing_path: Mapped[str | None] = mapped_column(String(500))
    design_json: Mapped[str | None] = mapped_column(Text)
    eval_json: Mapped[str | None] = mapped_column(Text)
    dxf_path: Mapped[str | None] = mapped_column(String(500))
    matched_rules_json: Mapped[str | None] = mapped_column(Text)
    generation_attempt: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    events: Mapped[list["AgentEvent"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    confirmations: Mapped[list["RuleConfirmation"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    step: Mapped[str] = mapped_column(String(80))
    outcome: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="events")


class RuleConfirmation(Base):
    __tablename__ = "rule_confirmations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    decided_by: Mapped[str] = mapped_column(String(80), default="engineer")
    approved: Mapped[int] = mapped_column(Integer)  # 1 confirm, 0 deny
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="confirmations")
