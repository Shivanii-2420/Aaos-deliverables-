import subprocess
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.engines.assurance.tool_adapters import (
    DeepEvalRunner,
    GarakRunner,
)


class GarakRunnerTests(unittest.TestCase):
    def test_parser_normalizes_only_failure_records(self):
        parsed = GarakRunner.parse_output(
            "probe detector PASS ok\n"
            "lmrc.Profanity riskywords.SurgeProfanityMentalDisability: "
            "FAIL ok on 17/20 (failure rate: 15%)\n"
            "not a result line\n"
        )
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["probe"], "lmrc.Profanity")
        self.assertEqual(parsed[0]["outcome"], "FAIL")

    def test_execution_uses_argument_list_and_preserves_artifacts(self):
        with tempfile.TemporaryDirectory() as output_dir:
            completed = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="probe detector FAIL hit\n",
                stderr="warning\n",
            )
            with patch.object(
                GarakRunner,
                "status",
                return_value={"status": "AVAILABLE", "version": "fixture"},
            ), patch(
                "backend.app.engines.assurance.tool_adapters.subprocess.run",
                return_value=completed,
            ) as run:
                result = GarakRunner.run(
                    "test",
                    "test.Blank",
                    ["promptinject.HijackHateHumansMini"],
                    Path(output_dir),
                    authorization_confirmed=True,
                )
            self.assertEqual(result.status, "COMPLETED")
            self.assertEqual(len(result.findings), 1)
            self.assertTrue(result.artifact_paths)
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual(run.call_args.args[0][0:3], [
                __import__("sys").executable, "-m", "garak"
            ])

    def test_unauthorized_target_is_not_executed(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(
                GarakRunner,
                "status",
                return_value={"status": "AVAILABLE", "version": "fixture"},
            ), patch(
                "backend.app.engines.assurance.tool_adapters.subprocess.run"
            ) as run:
                result = GarakRunner.run(
                    "test",
                    "test.Blank",
                    ["promptinject.HijackHateHumansMini"],
                    Path(output_dir),
                )
            self.assertEqual(result.status, "NOT_CONFIGURED")
            run.assert_not_called()

    def test_timeout_is_reported_as_timed_out(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(
                GarakRunner,
                "status",
                return_value={"status": "AVAILABLE", "version": "fixture"},
            ), patch(
                "backend.app.engines.assurance.tool_adapters.subprocess.run",
                side_effect=subprocess.TimeoutExpired("garak", 1, output=b"partial"),
            ):
                result = GarakRunner.run(
                    "test",
                    "test.Blank",
                    ["promptinject.HijackHateHumansMini"],
                    Path(output_dir),
                    authorization_confirmed=True,
                    timeout_seconds=1,
                )
            self.assertEqual(result.status, "TIMED_OUT")
            self.assertIn("timeout", result.error.lower())


class DeepEvalRunnerTests(unittest.TestCase):
    def test_judge_metric_requires_explicit_judge_and_confirmation(self):
        with patch.object(
            DeepEvalRunner,
            "status",
            return_value={"status": "AVAILABLE", "version": "fixture"},
        ):
            result = DeepEvalRunner.run(
                [{"input": "Question", "actual_output": "Answer"}],
                ["answer_relevancy"],
            )
        self.assertEqual(result.status, "NOT_CONFIGURED")
        self.assertIn("explicitly configured", result.error)

    def test_metric_results_are_preserved_when_one_case_fails(self):
        class FakeTestCase:
            def __init__(self, **kwargs):
                self.data = kwargs

        class FakeExactMatchMetric:
            def __init__(self, threshold):
                self.threshold = threshold
                self.score = None
                self.success = None
                self.reason = ""

            def measure(self, case):
                if case.data["input"] == "bad":
                    raise ValueError("fixture failure")
                self.score = float(
                    case.data.get("expected_output") == case.data["actual_output"]
                )
                self.success = self.score >= self.threshold
                self.reason = "fixture"

        deepeval = types.ModuleType("deepeval")
        metrics = types.ModuleType("deepeval.metrics")
        metrics.ExactMatchMetric = FakeExactMatchMetric
        test_case = types.ModuleType("deepeval.test_case")
        test_case.LLMTestCase = FakeTestCase
        with patch.object(
            DeepEvalRunner,
            "status",
            return_value={"status": "AVAILABLE", "version": "fixture"},
        ), patch.dict(
            "sys.modules",
            {
                "deepeval": deepeval,
                "deepeval.metrics": metrics,
                "deepeval.test_case": test_case,
            },
        ):
            result = DeepEvalRunner.run(
                [
                    {
                        "input": "good",
                        "actual_output": "yes",
                        "expected_output": "yes",
                    },
                    {
                        "input": "bad",
                        "actual_output": "no",
                        "expected_output": "yes",
                    },
                ],
                ["exact_match"],
                threshold=1,
            )
        self.assertEqual(result.status, "PARTIAL")
        self.assertEqual(
            [item["status"] for item in result.metrics],
            ["COMPLETED", "FAILED"],
        )
        self.assertEqual(result.metrics[0]["score"], 1.0)


if __name__ == "__main__":
    unittest.main()
