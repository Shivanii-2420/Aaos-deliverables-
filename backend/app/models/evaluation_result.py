from sqlalchemy import (
    ForeignKey,
    Text,
    Float,
    String,
    JSON
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from backend.app.database.base import Base


class EvaluationResult(Base):

    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    test_run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id")
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="COMPLETED",
        nullable=False,
    )

    error_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    evaluation_case_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_cases.id")
    )

    actual_response: Mapped[str] = mapped_column(
        Text
    )

    expected_response: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        default="unknown"
    )

    exact_match_score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    semantic_similarity_score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    metric_results: Mapped[dict] = mapped_column(
        JSON,
        default=dict
    )

    score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    hallucination_score: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    hallucination_detected: Mapped[float] = mapped_column(
        Float,
        default=0
    )
