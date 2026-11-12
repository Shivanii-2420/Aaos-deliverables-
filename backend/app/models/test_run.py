from sqlalchemy import String, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from backend.app.database.base import Base
from backend.app.core.time_utils import utcnow_naive


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    agent_version_id: Mapped[int] = mapped_column(
        ForeignKey("agent_versions.id")
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING"
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )

    dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluation_datasets.id"),
        nullable=True,
        index=True
    )

    dataset_version: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    dataset_snapshot_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )

    dataset_case_ids: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )

    dataset_snapshot: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )

    agent_version = relationship(
        "AgentVersion",
        back_populates="test_runs"
    )

    findings = relationship(
        "Finding",
        back_populates="test_run"
    )

    risk_scores = relationship(
        "RiskScore",
        back_populates="test_run"
    )

    execution_traces = relationship(
        "ExecutionTrace",
        back_populates="test_run"
    )

    attack_results = relationship(
        "AttackResult",
        back_populates="test_run"
    )