from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from backend.app.engines.assurance.egaa import (
    DEFAULT_TAXONOMY,
    DEFAULT_TEST_CATALOG,
    Evidence,
    estimate_evidence_gaps,
    run_adaptive_assurance,
)

BENCHMARK_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _evidence(
    risk_id: str,
    test_id: str,
    outcome: str = "pass",
    strength: float = 0.9,
    confidence: float = 0.9,
    mode: str = "simulated",
) -> Evidence:
    return Evidence(
        risk_id=risk_id,
        test_id=test_id,
        outcome=outcome,
        evidence_strength=strength,
        confidence=confidence,
        timestamp=BENCHMARK_TIME.isoformat(),
        provider="fixture",
        source="synthetic deterministic benchmark fixture",
        evidence_mode=mode,
    )


def _fixtures(scenario: str) -> tuple[list[Evidence], set[str]]:
    if scenario == "strong_existing_evidence":
        known = (
            "factuality", "prompt_injection", "sensitive_disclosure",
            "instruction_adherence", "harmful_output", "robustness",
        )
        return [
            _evidence(
                risk_id, "prior-suite", strength=1.0, confidence=1.0,
                mode="real",
            )
            for risk_id in known
        ], set()
    if scenario == "seeded_security_gap":
        existing = [
            _evidence(
                risk_id, "prior-quality", strength=1.0, confidence=1.0,
                mode="real",
            )
            for risk_id in ("factuality", "instruction_adherence", "robustness")
        ]
        return existing, {"prompt_injection"}
    if scenario == "contradictory_provider_evidence":
        known = [
            "factuality", "prompt_injection", "sensitive_disclosure",
            "instruction_adherence", "harmful_output", "robustness", "tool_misuse",
        ]
        existing = [
            _evidence(risk_id, "prior-suite", strength=1.0,
                      confidence=1.0, mode="real")
            for risk_id in known
        ]
        existing.extend([
            _evidence("provider_disagreement", "provider-a", "pass",
                      strength=1.0, confidence=1.0, mode="real"),
            _evidence("provider_disagreement", "provider-b", "fail",
                      strength=1.0, confidence=1.0, mode="real"),
        ])
        return existing, set()
    raise ValueError(f"Unknown benchmark scenario: {scenario}")


def _executor_for(
    test_id: str,
    seeded_failures: set[str],
) -> Callable[[], list[Evidence]]:
    definition = next(test for test in DEFAULT_TEST_CATALOG if test.test_id == test_id)

    def execute() -> list[Evidence]:
        return [
            _evidence(
                risk_id,
                test_id,
                "fail" if risk_id in seeded_failures else "pass",
                definition.expected_strength,
                definition.expected_confidence,
            )
            for risk_id in definition.risk_ids
        ]

    return execute


def _fixed_suite(
    initial: list[Evidence],
    seeded_failures: set[str],
) -> dict[str, object]:
    evidence = list(initial)
    for definition in DEFAULT_TEST_CATALOG:
        evidence.extend(_executor_for(definition.test_id, seeded_failures)())
    gaps = estimate_evidence_gaps(
        DEFAULT_TAXONOMY, evidence, now=BENCHMARK_TIME
    )
    return _strategy_summary(
        "fixed", evidence, gaps, len(DEFAULT_TEST_CATALOG), seeded_failures
    )


def _strategy_summary(
    name: str,
    evidence: list[Evidence],
    gaps: dict[str, dict[str, float | int | str | bool]],
    tests_executed: int,
    seeded_failures: set[str],
    estimated_cost: float | None = None,
) -> dict[str, object]:
    total_weight = sum(dimension.weight for dimension in DEFAULT_TAXONOMY)
    weighted_coverage = sum(
        dimension.weight * float(gaps[dimension.risk_id]["coverage"])
        for dimension in DEFAULT_TAXONOMY
    ) / total_weight
    critical_gaps = sum(
        1 for dimension in DEFAULT_TAXONOMY
        if dimension.weight >= 4
        and (
            float(gaps[dimension.risk_id]["gap_fraction"]) > dimension.threshold
            or bool(gaps[dimension.risk_id]["failed_evidence"])
        )
    )
    detected_failures = sorted(
        risk_id for risk_id in seeded_failures
        if bool(gaps[risk_id]["failed_evidence"])
    )
    return {
        "strategy": name,
        "tests_executed": tests_executed,
        "estimated_cost": round(
            estimated_cost if estimated_cost is not None
            else sum(test.cost for test in DEFAULT_TEST_CATALOG),
            4,
        ),
        "weighted_evidence_coverage": round(weighted_coverage, 4),
        "remaining_critical_evidence_gaps": critical_gaps,
        "seeded_high_risk_failures_detected": detected_failures,
        "evidence_gap_scores": gaps,
        "simulated": True,
    }


def run_synthetic_benchmark() -> dict[str, object]:
    scenarios = []
    for scenario in (
        "strong_existing_evidence",
        "seeded_security_gap",
        "contradictory_provider_evidence",
    ):
        initial, seeded_failures = _fixtures(scenario)
        executors = {
            test.test_id: _executor_for(test.test_id, seeded_failures)
            for test in DEFAULT_TEST_CATALOG
        }
        adaptive = run_adaptive_assurance(
            DEFAULT_TAXONOMY,
            DEFAULT_TEST_CATALOG,
            initial,
            executors,
            max_tests=2,
            max_seconds=10,
            target_type="mock",
            now=BENCHMARK_TIME,
        )
        fixed = _fixed_suite(initial, seeded_failures)
        adaptive_summary = _strategy_summary(
            "egaa_adaptive",
            [
                Evidence(**record)
                for record in adaptive["evidence"]
            ],
            adaptive["final_gaps"],
            int(adaptive["executed_tests"]),
            seeded_failures,
            float(adaptive["estimated_cost"]),
        )
        selection = [
            step["decision"]["selected_test"]
            for step in adaptive["selection_history"]
        ]
        scenarios.append({
            "scenario": scenario,
            "fixed": fixed,
            "adaptive": adaptive_summary,
            "adaptive_selected_tests": selection,
            "adaptive_stopped_reason": adaptive["stopped_reason"],
            "selection_reproducibility_key": selection,
        })
    return {
        "benchmark": "EGAA synthetic deterministic comparison",
        "timestamp_basis": BENCHMARK_TIME.isoformat(),
        "scenarios": scenarios,
        "limitations": [
            "All benchmark evidence and outcomes are synthetic and simulated.",
            "The fixtures establish selector behavior, not real-model safety or quality.",
            "Estimated cost units compare test effort only and are not currency.",
        ],
    }
