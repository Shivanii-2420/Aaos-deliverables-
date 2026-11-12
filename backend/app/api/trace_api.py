from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db
from backend.app.services.trace_service import TraceService
from backend.app.schemas.trace_schema import TraceResponse
from backend.app.schemas.trace_create_schema import TraceCreate

router = APIRouter(
    prefix="/traces",
    tags=["Flight Recorder"]
)


@router.get("")
def get_traces(
    test_run_id: int | None = None,
    db: Session = Depends(get_db)
):
    return TraceService.get_traces(db, test_run_id)


@router.post("", response_model=TraceResponse)
def create_trace(payload: TraceCreate, db: Session = Depends(get_db)):
    trace = TraceService.save_trace(db, payload.dict())
    return trace
