from sqlalchemy.orm import Session

from backend.app.models.risk_score import RiskScore
from backend.app.models.evaluation_result import EvaluationResult

from backend.app.engines.risk_engine.calculator import (
    RiskCalculator
)
from backend.app.models.attack_result import AttackResult


class RiskService:

    @staticmethod
    def generate(test_run_id: int, db: Session):

        results = (
            db.query(EvaluationResult)
            .filter(EvaluationResult.test_run_id == test_run_id)
            .all()
        )

        if not results:
            return None

        avg_score = sum(r.score for r in results) / len(results)

        hallucination_count = sum(1 for r in results if getattr(r, "hallucination_detected", 0))

        attack_successes = (
            db.query(AttackResult)
            .filter(AttackResult.test_run_id == test_run_id, AttackResult.success == True)
            .count()
        )

        scores = RiskCalculator.calculate(avg_score, hallucinations=hallucination_count, attack_successes=attack_successes)

        risk = RiskScore(
            test_run_id=test_run_id,
            security_score=scores["security_score"],
            reliability_score=scores["reliability_score"],
            overall_score=scores["overall_score"]
        )

        db.add(risk)

        db.commit()

        return risk
