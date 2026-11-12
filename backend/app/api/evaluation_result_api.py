from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from backend.app.database.dependencies import (
    get_db
)
from backend.app.models.evaluation_case import EvaluationCase
from backend.app.models.evaluation_result import (
    EvaluationResult
)
from backend.app.models.test_run import TestRun

router = APIRouter(
    prefix="/evaluation-results",
    tags=["Evaluation Results"]
)


@router.get("")
def get_results(
    test_run_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(EvaluationResult, EvaluationCase)
        .join(
            EvaluationCase,
            EvaluationCase.id == EvaluationResult.evaluation_case_id,
        )
    )
    if test_run_id is not None:
        if db.get(TestRun, test_run_id) is None:
            raise HTTPException(status_code=404, detail="Test run not found")
        query = query.filter(EvaluationResult.test_run_id == test_run_id)
    rows = query.order_by(EvaluationResult.id.desc()).limit(500).all()
    return [
        {
            "id": result.id,
            "test_run_id": result.test_run_id,
            "evaluation_case_id": result.evaluation_case_id,
            "prompt": case.prompt,
            "expected_response": result.expected_response,
            "actual_response": result.actual_response,
            "status": result.status,
            "error_type": result.error_type,
            "error_message": result.error_message,
            "provider": result.provider,
            "exact_match_score": result.exact_match_score,
            "similarity_score": result.semantic_similarity_score,
            "hallucination_score": result.hallucination_score,
            "hallucination_detected": bool(result.hallucination_detected),
            "metric_results": result.metric_results,
            "score": result.score,
        }
        for result, case in rows
    ]