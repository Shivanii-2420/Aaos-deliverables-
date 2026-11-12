from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel

from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db
from backend.app.models.finding import Finding
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/findings",
    tags=["Findings"]
)


@router.get("")
def get_findings(db: Session = Depends(get_db)):
    return db.query(Finding).all()


class FindingCreate(BaseModel):
    test_run_id: int
    finding: str
    severity: str


@router.post("")
def create_finding(payload: FindingCreate, db: Session = Depends(get_db)):
    f = Finding(
        test_run_id=payload.test_run_id,
        finding=payload.finding,
        severity=payload.severity
    )

    db.add(f)
    db.commit()
    db.refresh(f)

    return f
