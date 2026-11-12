from sqlalchemy.orm import Session

from backend.app.engines.attack_engine.attack_executor import (
    AttackExecutor
)

from backend.app.engines.attack_engine.attack_result_analyzer import (
    AttackResultAnalyzer
)

from backend.app.models.attack_result import AttackResult


class AttackService:

    @staticmethod
    def run_attacks(test_run_id: int | None = None, db: Session | None = None):

        execution_results = (
            AttackExecutor.execute()
        )

        final_results = []

        for result in execution_results:

            analysis = AttackResultAnalyzer.analyze(result)

            final_results.append(
                {
                    **result,
                    "risk": analysis.get("risk"),
                    "success": analysis.get("success", False),
                    "reason": analysis.get("reason")
                }
            )

        if db is not None and test_run_id is not None:
            for result in final_results:
                attack_result = AttackResult(
                    test_run_id=test_run_id,
                    attack_name=result.get("attack", "unknown"),
                    prompt=result.get("prompt", ""),
                    status=result.get("status", "UNKNOWN"),
                    response=result.get("response", ""),
                    risk=result.get("risk", "LOW"),
                    success=result.get("success", False),
                    reason=result.get("reason")
                )
                db.add(attack_result)
            db.commit()

        return final_results

    @staticmethod
    def get_attack_results(test_run_id: int | None, db: Session):
        query = db.query(AttackResult)

        if test_run_id is not None:
            query = query.filter(AttackResult.test_run_id == test_run_id)

        return query.all()
