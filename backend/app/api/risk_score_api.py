from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db
from backend.app.models.risk_score import RiskScore

router = APIRouter(
    prefix="/risk-scores",
    tags=["Risk Scores"]
)


@router.get("")
def get_risk_scores(db: Session = Depends(get_db)):
    return db.query(RiskScore).all()


class RiskScoreCreate(BaseModel):
    test_run_id: int
    security_score: float
    reliability_score: float
    overall_score: float


@router.post("")
def create_risk_score(payload: RiskScoreCreate, db: Session = Depends(get_db)):
    r = RiskScore(
        test_run_id=payload.test_run_id,
        security_score=payload.security_score,
        reliability_score=payload.reliability_score,
        overall_score=payload.overall_score
    )

    db.add(r)
    db.commit()
    db.refresh(r)

    return r
