from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class EvaluationCase(Base):

    __tablename__ = "evaluation_cases"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255)
    )

    prompt: Mapped[str] = mapped_column(
        Text
    )

    expected_response: Mapped[str] = mapped_column(
        Text
    )

    category: Mapped[str] = mapped_column(
        String(100)
    )

    test_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_runs.id"),
        nullable=True,
        index=True
    )

    dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluation_datasets.id"),
        nullable=True,
        index=True
    )

    tags: Mapped[list] = mapped_column(JSON, default=list)

    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    dataset = relationship("Dataset", back_populates="cases")
    