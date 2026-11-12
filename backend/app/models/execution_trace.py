from sqlalchemy import String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from backend.app.database.base import Base
from backend.app.core.time_utils import utcnow_naive


class ExecutionTrace(Base):
    __tablename__ = "execution_traces"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id"),
        nullable=True
    )
    prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    tokens_used: Mapped[int] = mapped_column(default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str] = mapped_column(String(1000), nullable=True)
    test_run = relationship("TestRun", back_populates="execution_traces")
