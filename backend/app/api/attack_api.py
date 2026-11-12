from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db
from backend.app.models.test_run import TestRun
from backend.app.services.attack_service import (
    AttackService
)
from backend.app.schemas.attack_result_schema import AttackResultResponse

router = APIRouter(
    prefix="/attacks",
    tags=["Attack Engine"]
)


@router.post("/run")
def run_attacks(
    test_run_id: int | None = None,
    db: Session = Depends(get_db)
):
    if test_run_id is not None:
        if db.query(TestRun).filter(TestRun.id == test_run_id).first() is None:
            raise HTTPException(status_code=404, detail="Test run not found")
    return AttackService.run_attacks(test_run_id, db)


@router.get("", response_model=list[AttackResultResponse])
def list_attack_results(
    test_run_id: int | None = None,
    db: Session = Depends(get_db)
):
    return AttackService.get_attack_results(test_run_id, db)