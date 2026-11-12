from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)

    test_run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id")
    )

    severity: Mapped[str] = mapped_column(
        String(50)
    )

    finding: Mapped[str] = mapped_column(
        String(2000)
    )

    test_run = relationship(
        "TestRun",
        back_populates="findings"
    )