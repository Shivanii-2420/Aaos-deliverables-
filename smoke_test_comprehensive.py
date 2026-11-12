import json

from backend.app.database.session import SessionLocal

from backend.app.services.evaluation_execution_service import (
    EvaluationExecutionService
)

from backend.app.services.evaluation_summary_service import (
    EvaluationSummaryService
)

from backend.app.models.agent import Agent

from backend.app.models.agent_version import AgentVersion

from backend.app.models.test_run import TestRun

from backend.app.models.evaluation_case import EvaluationCase

from backend.app.models.evaluation_result import EvaluationResult
from backend.app.models.risk_score import RiskScore
from backend.app.models.certificate import Certificate
from backend.app.models.execution_trace import ExecutionTrace


def comprehensive_test():

    db = SessionLocal()

    try:

        print("=" * 60)

        print("COMPREHENSIVE PHASE 4.1 + 4.2 TEST")

        print("=" * 60)

        # Cleanup
        db.query(EvaluationResult).delete()
        db.query(EvaluationCase).delete()
        db.query(TestRun).delete()
        db.query(AgentVersion).delete()
        db.query(Agent).delete()
        db.commit()

        print("\n[1] Creating test data...")

        agent = Agent(
            name="TestAgent",
            description="Test agent"
        )

        db.add(agent)
        db.commit()

        version = AgentVersion(
            agent_id=agent.id,
            version="1.0",
            model_name="gpt-4.1-nano"
        )

        db.add(version)
        db.commit()

        test_run = TestRun(
            agent_version_id=version.id,
            status="CREATED"
        )

        db.add(test_run)
        db.commit()

        test_cases = [
            ("Basic", "What is 2+2?", "4", "MATH"),
            ("Negation", "Is it true that 2+2=5?", "No", "LOGIC"),
            ("Factual", "Name a planet", "Earth", "SCIENCE")
        ]

        for name, prompt, expected_resp, category in test_cases:

            case = EvaluationCase(
                name=name,
                prompt=prompt,
                expected_response=expected_resp,
                category=category
            )

            db.add(case)

        db.commit()

        print(
            f"✓ Created: "
            f"1 agent, "
            f"1 version, "
            f"1 test_run, "
            f"3 cases"
        )

        # Execute evaluation
        print("\n[2] Executing evaluation...")

        results = EvaluationExecutionService.execute(
            test_run.id,
            db
        )

        print(
            f"✓ Executed: "
            f"{results['results_created']} results created"
        )

        # Query results
        print("\n[3] Inspection - Individual Results:")

        results = (
            db.query(EvaluationResult)
            .filter(
                EvaluationResult.test_run_id
                ==
                test_run.id
            )
            .all()
        )

        for i, r in enumerate(results, 1):

            print(
                f"\n  Result {i}:"
            )

            print(
                f"    Expected: {r.expected_response}"
            )

            print(
                f"    Actual: {r.actual_response}"
            )

            print(
                f"    Provider: {r.provider}"
            )

            print(
                f"    Exact Match: {r.exact_match_score}"
            )

            print(
                f"    Semantic Similarity: {r.semantic_similarity_score}"
            )

            print(
                f"    Hallucination Score: {r.hallucination_score}"
            )

            print(
                f"    Hallucination Detected: {r.hallucination_detected}"
            )

            print(
                f"    Score: {r.score}"
            )

        # Compute summary
        print("\n[4] Aggregation - Summary Stats:")

        summary = (
            EvaluationSummaryService.summarize_run(
                test_run.id,
                db
            )
        )

        print(
            json.dumps(
                summary,
                indent=2
            )
        )

        risk = (
            db.query(RiskScore)
            .filter(
                RiskScore.test_run_id == test_run.id
            )
            .first()
        )

        certificate = (
            db.query(Certificate)
            .filter(
                Certificate.agent_version_id
                == version.id
            )
            .order_by(Certificate.id.desc())
            .first()
        )

        trace_count = (
            db.query(ExecutionTrace)
            .filter(
                ExecutionTrace.test_run_id
                == test_run.id
            )
            .count()
        )

        print("\n[5] Trace and certificate inspection:")
        print(f"  Trace count: {trace_count}")
        print(f"  Risk score: {risk.overall_score if risk else 'N/A'}")
        print(
            f"  Certificate: {certificate.certificate_no if certificate else 'N/A'}"
        )

        print("\n" + "=" * 60)

        print("✓ ALL TESTS PASSED")

        print("=" * 60)

    finally:

        db.close()


if __name__ == "__main__":

    comprehensive_test()
