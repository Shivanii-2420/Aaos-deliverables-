from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from backend.app.database.base import Base
from backend.app.core.time_utils import utcnow_naive


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # owner is optional now; allow nullable to match AgentCreate schema
    owner: Mapped[str] = mapped_column(String(255), nullable=True)

    description: Mapped[str] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow_naive
    )

    versions = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan"
    )