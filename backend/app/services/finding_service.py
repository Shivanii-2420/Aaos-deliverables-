from sqlalchemy.orm import Session

from backend.app.models.finding import Finding
from backend.app.models.evaluation_result import EvaluationResult

from backend.app.engines.finding_engine.finding_generator import (
    FindingGenerator
)


class FindingService:

    @staticmethod
    def generate(test_run_id: int, db: Session):

        results = (
            db.query(EvaluationResult)
            .filter(EvaluationResult.test_run_id == test_run_id)
            .all()
        )

        findings_created = []

        for result in results:

            fd = FindingGenerator.generate(result.score)

            finding = Finding(
                test_run_id=test_run_id,
                severity=fd["severity"],
                finding=fd["finding"]
            )

            db.add(finding)

            findings_created.append(finding)

        db.commit()

        return findings_created
