from sqlalchemy.orm import Session

from backend.app.models.test_run import TestRun
from backend.app.models.evaluation_case import EvaluationCase
from backend.app.models.evaluation_result import EvaluationResult
from backend.app.models.finding import Finding
from backend.app.models.risk_score import RiskScore
from backend.app.services.certificate_service import (
    CertificateService
)

from backend.app.services.llm_router.fallback import FallbackRouter
from backend.app.engines.evaluation_engine.evaluator import Evaluator
from backend.app.engines.finding_engine.finding_generator import (
    FindingGenerator
)

from backend.app.engines.flight_recorder.trace_recorder import TraceRecorder
from backend.app.engines.flight_recorder.trace_store import TraceStore

from backend.app.engines.risk_engine.calculator import (
    RiskCalculator
)
from backend.app.models.attack_result import AttackResult
import logging
from types import SimpleNamespace
from backend.app.core.time_utils import utcnow_naive


logger = logging.getLogger(__name__)


class EvaluationExecutionService:

    @staticmethod
    def execute(test_run_id: int, db: Session):
        test_run = (
            db.query(TestRun)
            .filter(TestRun.id == test_run_id)
            .first()
        )

        if not test_run:
            raise Exception("TestRun not found")
        if test_run.status not in {"CREATED", "PENDING"}:
            raise ValueError(
                f"Test run cannot execute from status {test_run.status}"
            )

        claimed = (
            db.query(TestRun)
            .filter(
                TestRun.id == test_run_id,
                TestRun.status.in_(("CREATED", "PENDING")),
            )
            .update(
                {"status": "RUNNING"},
                synchronize_session=False,
            )
        )
        db.commit()
        if claimed != 1:
            db.refresh(test_run)
            raise ValueError(
                f"Test run cannot execute from status {test_run.status}"
            )
        test_run.status = "RUNNING"

        try:
            if (
                test_run.dataset_id is not None
                and test_run.dataset_snapshot is not None
            ):
                cases = [
                    SimpleNamespace(
                        id=item["id"],
                        prompt=item["prompt"],
                        expected_response=item["expected_response"],
                    )
                    for item in test_run.dataset_snapshot
                ]
            elif test_run.dataset_id is not None and test_run.dataset_case_ids is not None:
                cases = (
                    db.query(EvaluationCase)
                    .filter(EvaluationCase.id.in_(test_run.dataset_case_ids))
                    .order_by(EvaluationCase.id)
                    .all()
                    if test_run.dataset_case_ids else []
                )
            else:
                scoped_cases = (
                    db.query(EvaluationCase)
                    .filter(EvaluationCase.test_run_id == test_run_id)
                    .order_by(EvaluationCase.id)
                    .all()
                )
                cases = scoped_cases or (
                    db.query(EvaluationCase)
                    .filter(
                        EvaluationCase.test_run_id.is_(None),
                        EvaluationCase.dataset_id.is_(None),
                    )
                    .order_by(EvaluationCase.id)
                    .all()
                )

            results = []
            failed_cases = 0

            for case in cases:
                started_at = utcnow_naive()
                error_message = None
                actual = ""
                provider = "unknown"

                try:
                    llm_response = FallbackRouter.generate(case.prompt)
                    if (
                        not isinstance(llm_response, dict)
                        or not isinstance(llm_response.get("content"), str)
                    ):
                        raise ValueError("Invalid provider response")
                    actual = llm_response["content"]
                    provider = str(llm_response.get("provider", "unknown"))
                except Exception as ex:
                    error_type = type(ex).__name__
                    error_message = (
                        "Provider returned an invalid response."
                        if isinstance(ex, ValueError)
                        and str(ex) == "Invalid provider response"
                        else "Provider request failed."
                    )
                    logger.warning(
                        "Provider request failed for evaluation case %s (%s)",
                        case.id,
                        error_type
                    )
                else:
                    error_type = None

                ended_at = utcnow_naive()
                latency_ms = (
                    (ended_at - started_at).total_seconds() * 1000
                )

                trace = TraceRecorder.record(
                    prompt=case.prompt,
                    response=actual,
                    provider=provider,
                    started_at=started_at,
                    ended_at=ended_at,
                    latency_ms=latency_ms,
                    error=(
                        f"{error_message} ({error_type})"
                        if error_message else None
                    ),
                    test_run_id=test_run_id
                )

                TraceStore.save(db, trace)

                if error_message:
                    failed_cases += 1
                    result = EvaluationResult(
                        test_run_id=test_run_id,
                        evaluation_case_id=case.id,
                        expected_response=case.expected_response,
                        actual_response="",
                        provider=provider,
                        status="FAILED",
                        error_type=error_type,
                        error_message=error_message,
                        exact_match_score=0,
                        semantic_similarity_score=0,
                        metric_results={},
                        hallucination_score=0,
                        hallucination_detected=0,
                        score=0,
                    )
                else:
                    score_obj = Evaluator.evaluate(
                        expected=case.expected_response,
                        actual=actual
                    )
                    result = EvaluationResult(
                        test_run_id=test_run_id,
                        evaluation_case_id=case.id,
                        expected_response=case.expected_response,
                        actual_response=actual,
                        provider=provider,
                        status="COMPLETED",
                        exact_match_score=score_obj["exact_match"],
                        semantic_similarity_score=score_obj["semantic_similarity"],
                        metric_results=score_obj["metric_results"],
                        hallucination_score=score_obj["hallucination_score"],
                        hallucination_detected=score_obj["hallucination_detected"],
                        score=score_obj["score"],
                    )
                db.add(result)
                results.append(result)

            db.commit()

            successful_results = [result for result in results if result.status == "COMPLETED"]
            avg_score = (
                sum(r.score for r in successful_results)
                /
                len(successful_results)
            ) if successful_results else None

            hallucination_count = sum(
                1 for r in successful_results if getattr(r, "hallucination_detected", 0)
            )

            attack_success_count = (
                db.query(AttackResult)
                .filter(AttackResult.test_run_id == test_run_id)
                .filter(AttackResult.success.is_(True))
                .count()
            )

            if avg_score is not None:
                risk_data = RiskCalculator.calculate(
                    avg_score,
                    hallucinations=hallucination_count,
                    attack_successes=attack_success_count,
                )
                db.add(RiskScore(
                    test_run_id=test_run_id,
                    security_score=risk_data["security_score"],
                    reliability_score=risk_data["reliability_score"],
                    overall_score=risk_data["overall_score"],
                ))
                finding_data = FindingGenerator.generate(avg_score)
                db.add(Finding(
                    test_run_id=test_run_id,
                    severity=finding_data["severity"],
                    finding=finding_data["finding"],
                ))

            test_run.status = (
                "COMPLETED" if results and failed_cases == 0 else "FAILED"
            )
            test_run.end_time = utcnow_naive()
            db.commit()

            if test_run.status == "COMPLETED":
                CertificateService.create_certificate(test_run_id, db)

            response = {
                "test_run_id": test_run_id,
                "status": test_run.status,
                "total_cases": len(results),
                "completed_cases": len(successful_results),
                "failed_cases": failed_cases,
                "results_created": len(results),
                "average_score": round(avg_score, 4) if avg_score is not None else None,
            }
            if not results:
                response["failure_reason"] = "No evaluable cases were found."
            return response

        except Exception:
            db.rollback()
            if test_run.status != "COMPLETED":
                test_run.status = "FAILED"
                test_run.end_time = utcnow_naive()
                db.commit()
            raise
