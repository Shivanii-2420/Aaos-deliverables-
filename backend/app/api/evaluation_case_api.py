from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from backend.app.models.test_run import TestRun
from backend.app.database.dependencies import (
    get_db
)

from backend.app.schemas.evaluation_case_schema import (
    EvaluationCaseCreate,
    EvaluationCaseResponse
)

from backend.app.services.evaluation_case_service import (
    EvaluationCaseService
)

router = APIRouter(
    prefix="/evaluation-cases",
    tags=["Evaluation Cases"]
)


@router.post(
    "",
    response_model=EvaluationCaseResponse
)
def create_case(
    payload: EvaluationCaseCreate,
    db: Session = Depends(get_db)
):
    if payload.test_run_id is not None and db.get(TestRun, payload.test_run_id) is None:
        raise HTTPException(status_code=404, detail="Test run not found")
    if payload.dataset_id is not None:
        from backend.app.models.dataset import Dataset

        if db.get(Dataset, payload.dataset_id) is None:
            raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        return EvaluationCaseService.create_case(db, payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get(
    "",
    response_model=list[
        EvaluationCaseResponse
    ]
)
def get_cases(
    test_run_id: int | None = None,
    db: Session = Depends(get_db)
):

    if test_run_id is not None and db.get(TestRun, test_run_id) is None:
        raise HTTPException(status_code=404, detail="Test run not found")

    return EvaluationCaseService.get_cases(
        db,
        test_run_id
    )