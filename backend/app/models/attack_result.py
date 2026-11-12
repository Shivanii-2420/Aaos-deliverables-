from datetime import datetime

from sqlalchemy import String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base
from backend.app.core.time_utils import utcnow_naive


class AttackResult(Base):
    __tablename__ = "attack_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id")
    )
    attack_name: Mapped[str] = mapped_column(
        String(150)
    )
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50)
    )
    response: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    risk: Mapped[str] = mapped_column(
        String(50),
        default="LOW"
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive
    )

    test_run = relationship(
        "TestRun",
        back_populates="attack_results"
    )
