from backend.app.database.session import SessionLocal

from backend.app.services.evaluation_summary_service import (
    EvaluationSummaryService
)

import json


def test_summary():

    db = SessionLocal()

    try:

        # Get summary for test_run 1
        summary = (
            EvaluationSummaryService.summarize_run(
                test_run_id=1,
                db=db
            )
        )

        print(
            "=== EVALUATION SUMMARY ===="
        )

        print(
            json.dumps(
                summary,
                indent=2
            )
        )

        return summary

    finally:

        db.close()


if __name__ == "__main__":

    test_summary()
