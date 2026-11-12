from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db
from backend.app.models.test_run import TestRun
from backend.app.services.evaluation_execution_service import EvaluationExecutionService


router = APIRouter(
    prefix="/evaluation-execution",
    tags=["Evaluation Execution"]
)


@router.post("/{test_run_id}")
def run_evaluation(test_run_id: int, db: Session = Depends(get_db)):
    if db.query(TestRun).filter(TestRun.id == test_run_id).first() is None:
        raise HTTPException(status_code=404, detail="Test run not found")

    try:
        return EvaluationExecutionService.execute(test_run_id, db)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error