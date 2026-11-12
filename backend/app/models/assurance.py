from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.time_utils import utcnow_naive
from backend.app.database.base import Base


class AssuranceRunRecord(Base):
    __tablename__ = "assurance_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(60))
    target_type: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow_naive
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)


class AssuranceEvidenceRecord(Base):
    __tablename__ = "assurance_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    assurance_run_id: Mapped[int] = mapped_column(
        ForeignKey("assurance_runs.id"), index=True
    )
    risk_id: Mapped[str] = mapped_column(String(100), index=True)
    test_id: Mapped[str] = mapped_column(String(150), index=True)
    outcome: Mapped[str] = mapped_column(String(30))
    evidence_strength: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    execution_status: Mapped[str] = mapped_column(String(30))
    timestamp: Mapped[str] = mapped_column(String(40))
    provider: Mapped[str] = mapped_column(String(100), default="unknown")
    configuration: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(Text, default="")
    evidence_mode: Mapped[str] = mapped_column(String(30))
    execution_id: Mapped[str] = mapped_column(String(64), index=True)


class AssuranceDecisionRecord(Base):
    __tablename__ = "assurance_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assurance_run_id: Mapped[int] = mapped_column(
        ForeignKey("assurance_runs.id"), index=True
    )
    step_index: Mapped[int] = mapped_column()
    test_id: Mapped[str] = mapped_column(String(150))
    utility: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class ToolExecutionRecord(Base):
    __tablename__ = "tool_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id"), index=True
    )
    execution_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tool: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ended_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    configuration: Mapped[dict] = mapped_column(JSON, default=dict)
    findings: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_paths: Mapped[list] = mapped_column(JSON, default=list)
    original_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
