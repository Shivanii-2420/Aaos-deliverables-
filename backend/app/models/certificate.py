from sqlalchemy import String, ForeignKey, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True)

    agent_version_id: Mapped[int] = mapped_column(
        ForeignKey("agent_versions.id")
    )

    test_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_runs.id"),
        nullable=True,
        index=True,
    )

    certificate_no: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="ISSUED"
    )

    assessment_type: Mapped[str] = mapped_column(
        String(50),
        default="INTERNAL_UNSIGNED_ASSESSMENT",
        nullable=False,
    )

    score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    evidence: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    agent_version = relationship(
        "AgentVersion",
        back_populates="certificates"
    )
