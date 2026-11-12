import json
import hashlib

from sqlalchemy.orm import Session

from backend.app.models.agent_version import AgentVersion
from backend.app.models.test_run import TestRun
from backend.app.models.evaluation_result import EvaluationResult
from backend.app.models.finding import Finding
from backend.app.models.risk_score import RiskScore
from backend.app.models.execution_trace import ExecutionTrace
from backend.app.models.attack_result import AttackResult
from backend.app.core.time_utils import utcnow_naive


class EvidenceBuilder:

    @staticmethod
    def build(test_run_id: int, db: Session) -> tuple[str, float]:
        run = db.get(TestRun, test_run_id)
        if run is None:
            raise LookupError(f"Test run {test_run_id} was not found")
        version = db.get(AgentVersion, run.agent_version_id)
        evaluation_rows = (
            db.query(EvaluationResult)
            .filter(EvaluationResult.test_run_id == run.id)
            .order_by(EvaluationResult.id)
            .all()
        )
        if not evaluation_rows:
            raise ValueError("A test run with evaluation results is required")
        if any(result.status != "COMPLETED" for result in evaluation_rows):
            raise ValueError("All evaluation cases must be completed")
        score = sum(result.score for result in evaluation_rows) / len(evaluation_rows)

        findings = []
        risks = None
        results = []
        trace_count = 0
        attack_count = 0

        if run:
            findings = [
                {
                    "severity": f.severity,
                    "finding": f.finding
                }
                for f in (
                    db.query(Finding)
                    .filter(Finding.test_run_id == run.id)
                    .all()
                )
            ]

            risks = (
                db.query(RiskScore)
                .filter(RiskScore.test_run_id == run.id)
                .first()
            )

            results = [
                {
                    "case_id": r.evaluation_case_id,
                    "status": r.status,
                    "expected_response": r.expected_response,
                    "actual_response": r.actual_response,
                    "score": r.score,
                    "metric_results": getattr(r, "metric_results", {}),
                    "exact_match_score": r.exact_match_score,
                    "semantic_similarity_score": r.semantic_similarity_score,
                    "hallucination_score": r.hallucination_score,
                    "hallucination_detected": r.hallucination_detected,
                }
                for r in evaluation_rows
            ]

            trace_count = (
                db.query(ExecutionTrace)
                .filter(ExecutionTrace.test_run_id == run.id)
                .count()
            )

            attack_count = (
                db.query(AttackResult)
                .filter(AttackResult.test_run_id == run.id)
                .count()
            )

        evidence_payload = {
            "generated_at": utcnow_naive().isoformat() + "Z",
            "assessment_type": "INTERNAL_UNSIGNED_ASSESSMENT",
            "test_run_id": run.id,
            "agent_version_id": run.agent_version_id,
            "agent_version": version.version if version else None,
            "score": score,
            "findings": findings,
            "risk": {
                "security_score": risks.security_score if risks else None,
                "reliability_score": risks.reliability_score if risks else None,
                "overall_score": risks.overall_score if risks else None,
            } if risks else None,
            "evaluation_results": results,
            "execution_trace_count": trace_count,
            "attack_result_count": attack_count
        }

        # Add a simple report hash for traceability
        report_hash = hashlib.sha256(
            json.dumps(evidence_payload, sort_keys=True).encode()
        ).hexdigest()

        evidence_payload["report_hash"] = report_hash
        evidence_payload["auditor"] = None
        evidence_payload["certificate_signature"] = None

        return json.dumps(evidence_payload), score
