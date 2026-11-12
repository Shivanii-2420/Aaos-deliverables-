from fastapi import APIRouter
from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from backend.app.database.dependencies import (
    get_db
)

from backend.app.services.evaluation_execution_service import (
    EvaluationExecutionService
)

from backend.app.services.evaluation_summary_service import (
    EvaluationSummaryService
)
from backend.app.models.test_run import TestRun
from backend.app.engines.evaluation_engine.hallucination_engine import (
    HallucinationEvaluationEngine,
)
from backend.app.schemas.hallucination_schema import (
    HallucinationEvaluationRequest,
    HallucinationEvaluationResponse,
)

router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"]
)


@router.post(
    "/hallucination",
    response_model=HallucinationEvaluationResponse,
)
def evaluate_hallucinations(
    request: HallucinationEvaluationRequest,
):
    return HallucinationEvaluationEngine.evaluate(
        prompt=request.prompt,
        response=request.response,
        reference_context=request.reference_context,
    )


@router.post(
    "/run/{test_run_id}"
)
def execute_run(
    test_run_id: int,
    db: Session = Depends(get_db)
):
    if db.query(TestRun).filter(TestRun.id == test_run_id).first() is None:
        raise HTTPException(status_code=404, detail="Test run not found")

    try:
        results = EvaluationExecutionService.execute(
            test_run_id,
            db
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return results


@router.get(
    "/run/{test_run_id}/summary"
)
def get_run_summary(
    test_run_id: int,
    db: Session = Depends(get_db)
):
    if db.query(TestRun).filter(TestRun.id == test_run_id).first() is None:
        raise HTTPException(status_code=404, detail="Test run not found")

    summary = EvaluationSummaryService.summarize_run(
        test_run_id,
        db
    )

    return summary