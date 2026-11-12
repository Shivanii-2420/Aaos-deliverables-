from sqlalchemy import ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(primary_key=True)

    test_run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id")
    )

    security_score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    reliability_score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    overall_score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    test_run = relationship(
        "TestRun",
        back_populates="risk_scores"
    )