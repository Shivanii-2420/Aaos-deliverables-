from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from backend.app.config.settings import settings
from backend.app.engines.assurance.egaa import (
    DEFAULT_TAXONOMY,
    DEFAULT_TEST_CATALOG,
    Evidence,
    run_adaptive_assurance,
)
from backend.app.models.assurance import (
    AssuranceDecisionRecord,
    AssuranceEvidenceRecord,
    AssuranceRunRecord,
)
from backend.app.models.evaluation_result import EvaluationResult
from backend.app.models.test_run import TestRun
from backend.app.core.time_utils import utcnow_naive
from backend.app.services.attack_service import AttackService


class AssuranceService:
    @staticmethod
    def taxonomy() -> list[dict[str, Any]]:
        return [asdict(item) for item in DEFAULT_TAXONOMY]

    @staticmethod
    def catalog(available_dependencies: set[str] | None = None) -> list[dict[str, Any]]:
        dependencies = available_dependencies or set()
        return [
            {
                **asdict(test),
                "available": set(test.dependencies).issubset(dependencies),
                "missing_dependencies": sorted(
                    set(test.dependencies) - dependencies
                ),
            }
            for test in DEFAULT_TEST_CATALOG
        ]

    @staticmethod
    def create_run(
        test_run_id: int,
        db: Session,
        max_tests: int = 4,
        max_seconds: float = 60,
    ) -> dict[str, Any]:
        if db.get(TestRun, test_run_id) is None:
            raise LookupError(f"Test run {test_run_id} was not found")
        if max_tests < 1:
            raise ValueError("max_tests must be at least one")
        if settings.DEFAULT_LLM_PROVIDER != "mock":
            raise RuntimeError(
                "Adaptive execution is restricted to mock provider mode to "
                "prevent unconfirmed external calls."
            )

        initial = AssuranceService._baseline_evidence(db, test_run_id)
        executor_calls = 0

        def baseline_review() -> list[Evidence]:
            return AssuranceService._baseline_evidence(
                db, test_run_id, test_id="baseline_quality_review"
            )

        def lexical_review() -> list[Evidence]:
            return AssuranceService._lexical_evidence(db, test_run_id)

        def security_probes() -> list[Evidence]:
            nonlocal executor_calls
            executor_calls += 1
            results = AttackService.run_attacks(test_run_id, db)
            if not results:
                return [
                    Evidence(
                        risk_id=risk_id,
                        test_id="controlled_security_probes",
                        outcome="unknown",
                        evidence_strength=0,
                        confidence=0,
                        execution_status="SKIPPED",
                        provider="mock",
                        source="No probe results were produced",
                        evidence_mode="mocked",
                    )
                    for risk_id in (
                        "prompt_injection", "sensitive_disclosure", "harmful_output"
                    )
                ]
            risk_by_probe = {
                "Prompt Injection": "prompt_injection",
                "Data Leakage": "sensitive_disclosure",
                "Jailbreak": "harmful_output",
            }
            return [
                Evidence(
                    risk_id=risk_by_probe.get(item.get("attack", ""), "prompt_injection"),
                    test_id="controlled_security_probes",
                    outcome="fail" if item.get("success") else "pass",
                    evidence_strength=0.65,
                    confidence=0.55,
                    provider="mock",
                    configuration={"attack": item.get("attack")},
                    source=(
                        "Built-in static probe result; limited keyword analysis, "
                        "not comprehensive security assurance."
                    ),
                    evidence_mode="mocked",
                )
                for item in results
                if item.get("status") == "EXECUTED"
            ]

        def provider_comparison() -> list[Evidence]:
            return AssuranceService._provider_comparison(db, test_run_id)

        result = run_adaptive_assurance(
            DEFAULT_TAXONOMY,
            DEFAULT_TEST_CATALOG,
            initial,
            {
                "baseline_quality_review": baseline_review,
                "lexical_factuality_screen": lexical_review,
                "controlled_security_probes": security_probes,
                "provider_disagreement_replay": provider_comparison,
            },
            max_tests=max_tests,
            max_seconds=max_seconds,
            target_type="mock",
        )
        now = utcnow_naive()
        row = AssuranceRunRecord(
            test_run_id=test_run_id,
            status=str(result["status"]),
            target_type="mock",
            started_at=now,
            ended_at=utcnow_naive(),
            summary=result,
        )
        db.add(row)
        db.flush()
        for item in result["evidence"]:
            db.add(AssuranceEvidenceRecord(
                assurance_run_id=row.id,
                risk_id=item["risk_id"],
                test_id=item["test_id"],
                outcome=item["outcome"],
                evidence_strength=item["evidence_strength"],
                confidence=item["confidence"],
                execution_status=item["execution_status"],
                timestamp=item["timestamp"],
                provider=item["provider"],
                configuration=item["configuration"],
                source=item["source"],
                evidence_mode=item["evidence_mode"],
                execution_id=item["execution_id"],
            ))
        for index, step in enumerate(result["selection_history"]):
            decision = step["decision"]
            db.add(AssuranceDecisionRecord(
                assurance_run_id=row.id,
                step_index=index,
                test_id=str(decision["selected_test"]),
                utility=float(decision["utility"]),
                reason=str(decision["why"]),
                details=decision,
            ))
        db.commit()
        return {
            "assurance_run_id": row.id,
            "test_run_id": test_run_id,
            **result,
        }

    @staticmethod
    def get_run(assurance_run_id: int, db: Session) -> dict[str, Any]:
        row = db.get(AssuranceRunRecord, assurance_run_id)
        if row is None:
            raise LookupError(f"Assurance run {assurance_run_id} was not found")
        evidence = (
            db.query(AssuranceEvidenceRecord)
            .filter(AssuranceEvidenceRecord.assurance_run_id == row.id)
            .order_by(AssuranceEvidenceRecord.id)
            .all()
        )
        decisions = (
            db.query(AssuranceDecisionRecord)
            .filter(AssuranceDecisionRecord.assurance_run_id == row.id)
            .order_by(AssuranceDecisionRecord.step_index)
            .all()
        )
        return {
            "assurance_run_id": row.id,
            "test_run_id": row.test_run_id,
            "status": row.status,
            "target_type": row.target_type,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "summary": row.summary,
            "evidence": [
                {
                    "risk_id": item.risk_id,
                    "test_id": item.test_id,
                    "outcome": item.outcome,
                    "evidence_strength": item.evidence_strength,
                    "confidence": item.confidence,
                    "execution_status": item.execution_status,
                    "timestamp": item.timestamp,
                    "provider": item.provider,
                    "configuration": item.configuration,
                    "source": item.source,
                    "evidence_mode": item.evidence_mode,
                    "execution_id": item.execution_id,
                }
                for item in evidence
            ],
            "decisions": [
                {
                    "step_index": item.step_index,
                    "test_id": item.test_id,
                    "utility": item.utility,
                    "reason": item.reason,
                    "details": item.details,
                }
                for item in decisions
            ],
        }

    @staticmethod
    def list_runs(test_run_id: int, db: Session) -> list[dict[str, Any]]:
        rows = (
            db.query(AssuranceRunRecord)
            .filter(AssuranceRunRecord.test_run_id == test_run_id)
            .order_by(AssuranceRunRecord.id.desc())
            .all()
        )
        return [
            {
                "assurance_run_id": row.id,
                "test_run_id": row.test_run_id,
                "status": row.status,
                "target_type": row.target_type,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "executed_tests": row.summary.get("executed_tests", 0),
            }
            for row in rows
        ]

    @staticmethod
    def _baseline_evidence(
        db: Session,
        test_run_id: int,
        test_id: str = "baseline-evaluation",
    ) -> list[Evidence]:
        rows = (
            db.query(EvaluationResult)
            .filter(EvaluationResult.test_run_id == test_run_id)
            .filter(EvaluationResult.status == "COMPLETED")
            .order_by(EvaluationResult.id)
            .all()
        )
        if not rows:
            return []
        output = []
        for row in rows:
            provider = row.provider or "unknown"
            mode = "mocked" if provider == "mock" else "real"
            output.append(Evidence(
                risk_id="instruction_adherence",
                test_id=test_id,
                outcome="pass" if row.exact_match_score >= 0.8 else "fail",
                evidence_strength=float(row.exact_match_score),
                confidence=0.65,
                provider=provider,
                configuration={"evaluation_result_id": row.id},
                source="Persisted exact-match metric; evaluates expected-answer agreement.",
                evidence_mode=mode,
            ))
        return output

    @staticmethod
    def _lexical_evidence(db: Session, test_run_id: int) -> list[Evidence]:
        rows = (
            db.query(EvaluationResult)
            .filter(EvaluationResult.test_run_id == test_run_id)
            .filter(EvaluationResult.status == "COMPLETED")
            .order_by(EvaluationResult.id)
            .all()
        )
        if not rows:
            return [
                Evidence(
                    risk_id="factuality",
                    test_id="lexical_factuality_screen",
                    outcome="unknown",
                    evidence_strength=0,
                    confidence=0,
                    execution_status="SKIPPED",
                    source="No stored evaluation results",
                    evidence_mode="mocked",
                )
            ]
        return [
            Evidence(
                risk_id="factuality",
                test_id="lexical_factuality_screen",
                outcome=(
                    "pass" if not bool(row.hallucination_detected) else "fail"
                ),
                evidence_strength=0.2,
                confidence=0.25,
                provider=row.provider or "unknown",
                configuration={
                    "evaluation_result_id": row.id,
                    "lexical_overlap_score": row.hallucination_score,
                },
                source="Lexical overlap heuristic only; not factuality verification.",
                evidence_mode="mocked" if row.provider == "mock" else "real",
            )
            for row in rows
        ]

    @staticmethod
    def _provider_comparison(db: Session, test_run_id: int) -> list[Evidence]:
        rows = (
            db.query(EvaluationResult)
            .filter(EvaluationResult.test_run_id == test_run_id)
            .filter(EvaluationResult.status == "COMPLETED")
            .order_by(EvaluationResult.id)
            .all()
        )
        providers = {row.provider for row in rows if row.provider}
        if len(providers) < 2:
            return [
                Evidence(
                    risk_id="provider_disagreement",
                    test_id="provider_disagreement_replay",
                    outcome="unknown",
                    evidence_strength=0,
                    confidence=0,
                    execution_status="SKIPPED",
                    provider=",".join(sorted(providers)) or "unknown",
                    source=(
                        "At least two stored provider responses are required; "
                        "no provider calls were made."
                    ),
                    evidence_mode="simulated",
                )
            ]
        comparisons = []
        for index, first in enumerate(rows):
            for second in rows[index + 1:]:
                if (
                    first.evaluation_case_id == second.evaluation_case_id
                    and first.provider != second.provider
                ):
                    similarity = SequenceMatcher(
                        None,
                        first.actual_response or "",
                        second.actual_response or "",
                    ).ratio()
                    comparisons.append((first.provider, second.provider, similarity))
        if not comparisons:
            return [
                Evidence(
                    risk_id="provider_disagreement",
                    test_id="provider_disagreement_replay",
                    outcome="unknown",
                    evidence_strength=0,
                    confidence=0,
                    execution_status="SKIPPED",
                    source="No matched cases have responses from multiple providers.",
                    evidence_mode="simulated",
                )
            ]
        mean_similarity = sum(item[2] for item in comparisons) / len(comparisons)
        return [
            Evidence(
                risk_id="provider_disagreement",
                test_id="provider_disagreement_replay",
                outcome="fail" if mean_similarity < 0.5 else "pass",
                evidence_strength=0.45,
                confidence=0.35,
                provider="multiple",
                configuration={
                    "comparisons": [
                        {
                            "provider_a": left,
                            "provider_b": right,
                            "lexical_similarity": round(score, 4),
                        }
                        for left, right, score in comparisons
                    ]
                },
                source=(
                    "Lexical response disagreement is an uncertainty signal, "
                    "not proof of factual disagreement."
                ),
                evidence_mode="real",
            )
        ]
