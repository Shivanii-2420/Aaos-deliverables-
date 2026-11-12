import unittest
from datetime import datetime, timedelta, timezone

from backend.app.engines.assurance.benchmark import run_synthetic_benchmark
from backend.app.engines.assurance.egaa import (
    DEFAULT_TAXONOMY,
    DEFAULT_TEST_CATALOG,
    Evidence,
    RiskDimension,
    TestDefinition,
    estimate_evidence_gaps,
    run_adaptive_assurance,
    select_next_test,
)

NOW = datetime(2026, 11, 11, tzinfo=timezone.utc)


def evidence(
    risk_id,
    test_id="fixture",
    outcome="pass",
    strength=0.9,
    confidence=0.9,
    timestamp=None,
    status="COMPLETED",
):
    return Evidence(
        risk_id=risk_id,
        test_id=test_id,
        outcome=outcome,
        evidence_strength=strength,
        confidence=confidence,
        execution_status=status,
        timestamp=(timestamp or NOW).isoformat(),
        evidence_mode="real",
    )


class EvidenceGapTests(unittest.TestCase):
    def setUp(self):
        self.taxonomy = (RiskDimension("risk", "fixture", 5, ("test",)),)

    def test_missing_failed_and_skipped_evidence_never_claims_assurance(self):
        missing = estimate_evidence_gaps(self.taxonomy, [], now=NOW)["risk"]
        failed = estimate_evidence_gaps(
            self.taxonomy, [evidence("risk", outcome="fail")], now=NOW
        )["risk"]
        skipped = estimate_evidence_gaps(
            self.taxonomy,
            [evidence("risk", outcome="pass", status="SKIPPED")],
            now=NOW,
        )["risk"]
        self.assertEqual(missing["coverage"], 0)
        self.assertEqual(skipped["coverage"], 0)
        self.assertGreater(failed["coverage"], 0)
        self.assertTrue(failed["failed_evidence"])

    def test_old_weak_and_mocked_evidence_has_less_weight(self):
        strong = estimate_evidence_gaps(
            self.taxonomy, [evidence("risk")], now=NOW
        )["risk"]
        old = estimate_evidence_gaps(
            self.taxonomy,
            [evidence("risk", timestamp=NOW - timedelta(days=30))],
            now=NOW,
        )["risk"]
        weak = estimate_evidence_gaps(
            self.taxonomy,
            [evidence("risk", confidence=0.2)],
            now=NOW,
        )["risk"]
        self.assertGreater(strong["coverage"], old["coverage"])
        self.assertGreater(strong["coverage"], weak["coverage"])

    def test_contradictory_evidence_increases_uncertainty(self):
        single = evidence("risk", test_id="one")
        conflicting = [
            single,
            evidence("risk", test_id="two", outcome="fail"),
        ]
        gap = estimate_evidence_gaps(self.taxonomy, conflicting, now=NOW)["risk"]
        self.assertTrue(gap["contradiction"])
        self.assertEqual(gap["contradiction_level"], 1.0)
        self.assertGreater(gap["uncertainty"], 0.1)

    def test_failed_or_unknown_executions_do_not_add_coverage(self):
        results = estimate_evidence_gaps(
            self.taxonomy,
            [
                evidence("risk", status="FAILED"),
                evidence("risk", outcome="unknown"),
            ],
            now=NOW,
        )
        self.assertEqual(results["risk"]["coverage"], 0)


class AdaptiveSelectorTests(unittest.TestCase):
    def test_selection_is_deterministic_and_explains_excluded_tests(self):
        taxonomy = DEFAULT_TAXONOMY
        decision = select_next_test(
            DEFAULT_TEST_CATALOG, taxonomy, [], now=NOW
        )
        repeat = select_next_test(
            DEFAULT_TEST_CATALOG, taxonomy, [], now=NOW
        )
        self.assertEqual(decision["selected_test"], repeat["selected_test"])
        self.assertTrue(decision["why"])
        self.assertTrue(decision["expected_evidence"])
        self.assertEqual(len(decision["considered"]), len(DEFAULT_TEST_CATALOG))

    def test_security_gap_prioritizes_security_over_baseline_quality(self):
        initial = [
            evidence(risk_id, test_id="prior")
            for risk_id in (
                "factuality", "instruction_adherence", "robustness",
            )
        ]
        decision = select_next_test(
            DEFAULT_TEST_CATALOG,
            DEFAULT_TAXONOMY,
            initial,
            now=NOW,
        )
        self.assertEqual(decision["selected_test"], "controlled_security_probes")

    def test_adaptive_loop_records_selection_and_failed_risk(self):
        taxonomy = (
            RiskDimension("critical", "critical", 5, ("test",), threshold=0.2),
        )
        test = TestDefinition("test", ("critical",), 0.8, 0.8, 1)

        def execute():
            return [evidence("critical", "test", outcome="fail")]

        result = run_adaptive_assurance(
            taxonomy, (test,), (), {"test": execute},
            max_tests=1, now=NOW,
        )
        self.assertEqual(result["executed_tests"], 1)
        self.assertEqual(result["status"], "UNRESOLVED_CRITICAL_RISK")
        self.assertTrue(result["selection_history"][0]["decision"]["why"])
        self.assertTrue(result["unresolved_risks"][0]["failed_evidence"])

    def test_missing_dependency_is_reported_not_executed(self):
        taxonomy = (RiskDimension("risk", "risk", 5, ("evidence",)),)
        test = TestDefinition(
            "external", ("risk",), 0.8, 0.8, 1,
            dependencies=("optional_tool",),
        )
        self.assertIsNone(select_next_test(
            (test,), taxonomy, (), available_dependencies=(), now=NOW
        ))

    def test_budget_and_no_eligible_test_stopping(self):
        taxonomy = DEFAULT_TAXONOMY
        executors = {
            test.test_id: lambda test=test: [
                evidence(risk, test.test_id, timestamp=NOW)
                for risk in test.risk_ids
            ]
            for test in DEFAULT_TEST_CATALOG
        }
        budget_result = run_adaptive_assurance(
            taxonomy, DEFAULT_TEST_CATALOG, (), executors,
            max_tests=1, now=NOW,
        )
        self.assertEqual(budget_result["stopped_reason"], "maximum test budget reached")

        no_eligible = run_adaptive_assurance(
            taxonomy, (), (), {}, max_tests=5, now=NOW
        )
        self.assertEqual(no_eligible["stopped_reason"], "no eligible tests remain")

    def test_executor_timeout_is_recorded_without_assurance_credit(self):
        taxonomy = (RiskDimension("risk", "risk", 5, ("evidence",)),)
        test = TestDefinition("timeout", ("risk",), 0.8, 0.8, 1)

        def timeout():
            raise TimeoutError("fixture timeout")

        result = run_adaptive_assurance(
            taxonomy, (test,), (), {"timeout": timeout},
            max_tests=1, now=NOW,
        )
        self.assertEqual(result["evidence"][0]["execution_status"], "TIMED_OUT")
        self.assertEqual(result["final_gaps"]["risk"]["coverage"], 0)

    def test_critical_finding_stops_selection_separately_from_execution_error(self):
        taxonomy = (
            RiskDimension("critical", "critical", 5, ("test",), threshold=0.2),
        )
        test = TestDefinition(
            "critical_test", ("critical",), 0.8, 0.8, 1,
            critical_failure_stops=True,
        )

        finding = run_adaptive_assurance(
            taxonomy,
            (test,),
            (),
            {"critical_test": lambda: [
                evidence("critical", "critical_test", outcome="fail")
            ]},
            max_tests=3,
            now=NOW,
        )
        self.assertEqual(
            finding["stopped_reason"],
            "critical risk finding detected",
        )
        self.assertEqual(finding["executed_tests"], 1)

        execution_error = run_adaptive_assurance(
            taxonomy,
            (test,),
            (),
            {"critical_test": lambda: (_ for _ in ()).throw(
                RuntimeError("fixture")
            )},
            max_tests=3,
            now=NOW,
        )
        self.assertEqual(
            execution_error["stopped_reason"],
            "critical test execution failure",
        )
        self.assertEqual(execution_error["executed_tests"], 1)


class SyntheticBenchmarkTests(unittest.TestCase):
    def test_three_benchmark_scenarios_are_reproducible_and_report_tradeoffs(self):
        first = run_synthetic_benchmark()
        second = run_synthetic_benchmark()
        self.assertEqual(len(first["scenarios"]), 3)
        self.assertEqual(
            [item["adaptive_selected_tests"] for item in first["scenarios"]],
            [item["adaptive_selected_tests"] for item in second["scenarios"]],
        )
        self.assertEqual(
            [item["adaptive_stopped_reason"] for item in first["scenarios"]],
            [item["adaptive_stopped_reason"] for item in second["scenarios"]],
        )
        security = first["scenarios"][1]
        self.assertIn(
            "prompt_injection",
            security["adaptive"]["seeded_high_risk_failures_detected"],
        )
        contradiction = first["scenarios"][2]
        self.assertEqual(
            contradiction["adaptive_selected_tests"][0],
            "provider_disagreement_replay",
        )
        for scenario in first["scenarios"]:
            self.assertTrue(scenario["fixed"]["simulated"])
            self.assertTrue(scenario["adaptive"]["simulated"])
            self.assertIn("weighted_evidence_coverage", scenario["fixed"])
            self.assertIn("remaining_critical_evidence_gaps", scenario["adaptive"])


if __name__ == "__main__":
    unittest.main()
