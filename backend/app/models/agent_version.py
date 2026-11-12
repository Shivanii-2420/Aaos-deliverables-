from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from backend.app.database.base import Base
from backend.app.core.time_utils import utcnow_naive


class AgentVersion(Base):
    __tablename__ = "agent_versions"

    id: Mapped[int] = mapped_column(primary_key=True)

    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id")
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    prompt_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive
    )

    agent = relationship(
        "Agent",
        back_populates="versions"
    )

    test_runs = relationship(
        "TestRun",
        back_populates="agent_version"
    )

    certificates = relationship(
        "Certificate",
        back_populates="agent_version"
    )