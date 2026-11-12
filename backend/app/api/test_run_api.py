from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db

from backend.app.schemas.test_run_schema import (
    TestRunResponse
)

from backend.app.services.test_run_service import (
    TestRunService
)

router = APIRouter(
    prefix="/versions",
    tags=["Test Runs"]
)


@router.post(
    "/{version_id}/runs",
    response_model=TestRunResponse
)
def create_run(
    version_id: int,
    db: Session = Depends(get_db)
):

    return TestRunService.create_test_run(
        db,
        version_id
    )


@router.get(
    "/{version_id}/runs",
    response_model=list[TestRunResponse]
)
def get_runs(
    version_id: int,
    db: Session = Depends(get_db)
):

    return TestRunService.get_test_runs(
        db,
        version_id
    )