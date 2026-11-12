from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4


@dataclass
class ToolResult:
    tool: str
    status: str
    execution_id: str = field(default_factory=lambda: uuid4().hex)
    version: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_seconds: float = 0.0
    findings: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    original_metadata: dict[str, Any] = field(default_factory=dict)


def _package_version(package: str, module: str) -> str | None:
    try:
        importlib.util.find_spec(module)
    except (ImportError, ValueError):
        return None
    if importlib.util.find_spec(module) is None:
        return None
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "installed-version-unknown"


class GarakRunner:
    """Optional runner based on Garak's documented `python -m garak` CLI."""

    SUPPORTED_PROBES = frozenset({
        "promptinject.HijackHateHumansMini",
        "lmrc.Profanity",
    })
    SAFE_TEST_TARGETS = frozenset({"test.Blank", "test.Repeat"})
    MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
    FINDING_PATTERN = re.compile(
        r"^\s*(?P<probe>\S+)\s+(?P<detector>\S+)\s+"
        r"(?P<outcome>PASS|FAIL)\b(?P<details>.*)$",
        re.IGNORECASE,
    )

    @classmethod
    def status(cls) -> dict[str, Any]:
        version = _package_version("garak", "garak")
        return {
            "tool": "garak",
            "status": "AVAILABLE" if version else "NOT_INSTALLED",
            "version": version,
            "execution_interface": "python -m garak CLI",
            "supported_probes": sorted(cls.SUPPORTED_PROBES),
            "safe_test_targets": sorted(cls.SAFE_TEST_TARGETS),
        }

    @classmethod
    def parse_output(cls, output: str) -> list[dict[str, str]]:
        findings = []
        for line in output.splitlines():
            match = cls.FINDING_PATTERN.match(line)
            if match:
                item = match.groupdict()
                item["outcome"] = item["outcome"].upper()
                item["details"] = item["details"].strip()
                if item["outcome"] == "FAIL":
                    findings.append(item)
        return findings

    @classmethod
    def run(
        cls,
        model_type: str,
        model_name: str,
        probes: Sequence[str],
        output_root: Path,
        authorization_confirmed: bool = False,
        external_target_confirmed: bool = False,
        timeout_seconds: int = 120,
    ) -> ToolResult:
        tool_status = cls.status()
        result = ToolResult(
            tool="garak",
            status=tool_status["status"],
            version=tool_status["version"],
        )
        if tool_status["status"] == "NOT_INSTALLED":
            result.error = "Garak is not installed in the selected Python environment."
            return result
        if not authorization_confirmed:
            result.status = "NOT_CONFIGURED"
            result.error = "Explicit authorization confirmation is required."
            return result
        if not probes or any(probe not in cls.SUPPORTED_PROBES for probe in probes):
            result.status = "FAILED"
            result.error = "Probe selection contains an unsupported probe."
            return result
        if not cls.MODEL_PATTERN.fullmatch(model_name):
            result.status = "FAILED"
            result.error = "Target identifier contains invalid characters."
            return result
        if model_type == "test":
            if model_name not in cls.SAFE_TEST_TARGETS:
                result.status = "FAILED"
                result.error = "The Garak test generator must use an allowlisted target."
                return result
        elif not external_target_confirmed:
            result.status = "NOT_CONFIGURED"
            result.error = (
                "External model execution requires separate explicit confirmation."
            )
            return result
        if not 1 <= timeout_seconds <= 600:
            result.status = "FAILED"
            result.error = "Timeout must be between 1 and 600 seconds."
            return result

        run_dir = output_root.resolve() / uuid4().hex
        run_dir.mkdir(parents=True, exist_ok=False)
        report_prefix = str(run_dir / "garak")
        command = [
            sys.executable,
            "-m",
            "garak",
            "--model_type",
            model_type,
            "--model_name",
            model_name,
            "--probes",
            ",".join(probes),
            "--report_prefix",
            report_prefix,
        ]
        result.status = "RUNNING"
        result.started_at = datetime.now(timezone.utc).isoformat()
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                shell=False,
                env=None,
            )
            stdout = _redact(completed.stdout[-1_000_000:])
            stderr = _redact(completed.stderr[-200_000:])
            (run_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
            (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
            result.original_metadata = {
                "exit_code": completed.returncode,
                "stdout_tail": stdout[-20_000:],
                "stderr_tail": stderr[-10_000:],
                "command": command[:-1] + ["<report-prefix>"],
            }
            result.findings = cls.parse_output(stdout)
            result.status = "COMPLETED" if completed.returncode == 0 else "FAILED"
            if completed.returncode != 0:
                result.error = f"Garak exited with code {completed.returncode}."
            for path in run_dir.iterdir():
                if path.is_file():
                    result.artifact_paths.append(str(path))
        except subprocess.TimeoutExpired as error:
            result.status = "TIMED_OUT"
            result.error = f"Garak exceeded the {timeout_seconds}-second timeout."
            result.original_metadata = {
                "stdout": _decode_output(error.stdout, 200_000),
                "stderr": _decode_output(error.stderr, 100_000),
            }
        except OSError as error:
            result.status = "FAILED"
            result.error = f"Garak could not be started ({type(error).__name__})."
        finally:
            result.duration_seconds = round(time.monotonic() - started, 4)
            result.ended_at = datetime.now(timezone.utc).isoformat()
        return result


def _decode_output(value: str | bytes | None, limit: int) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return _redact(value[-limit:])


def _redact(value: str) -> str:
    for key, secret in os.environ.items():
        if secret and len(secret) >= 8 and any(
            word in key.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")
        ):
            value = value.replace(secret, "[REDACTED]")
    return re.sub(
        r"(?i)(sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{20,})",
        "[REDACTED]",
        value,
    )


class DeepEvalRunner:
    """Runs documented DeepEval metrics, gating any judge-backed metric."""

    METRICS = frozenset({"exact_match", "answer_relevancy"})

    @classmethod
    def status(cls) -> dict[str, Any]:
        version = _package_version("deepeval", "deepeval")
        return {
            "tool": "deepeval",
            "status": "AVAILABLE" if version else "NOT_INSTALLED",
            "version": version,
            "supported_metrics": sorted(cls.METRICS),
            "judge_metrics": ["answer_relevancy"],
        }

    @classmethod
    def run(
        cls,
        cases: Sequence[Mapping[str, str]],
        metrics: Sequence[str],
        threshold: float = 0.5,
        judge_model: str | None = None,
        allow_judge_calls: bool = False,
    ) -> ToolResult:
        status = cls.status()
        result = ToolResult(
            tool="deepeval",
            status=status["status"],
            version=status["version"],
        )
        if status["status"] == "NOT_INSTALLED":
            result.error = "DeepEval is not installed in the selected Python environment."
            return result
        if not cases or len(cases) > 100:
            result.status = "FAILED"
            result.error = "Supply between 1 and 100 prompt/response cases."
            return result
        if not metrics or any(metric not in cls.METRICS for metric in metrics):
            result.status = "FAILED"
            result.error = "Metric selection contains an unsupported metric."
            return result
        if not 0 <= threshold <= 1:
            result.status = "FAILED"
            result.error = "Threshold must be between 0 and 1."
            return result
        judge_requested = "answer_relevancy" in metrics
        if judge_requested and (not allow_judge_calls or not judge_model):
            result.status = "NOT_CONFIGURED"
            result.error = (
                "Answer Relevancy requires an explicitly configured judge model "
                "and external-call confirmation."
            )
            return result

        try:
            from deepeval.metrics import ExactMatchMetric
            from deepeval.test_case import LLMTestCase
        except (ImportError, ModuleNotFoundError):
            result.status = "NOT_INSTALLED"
            result.error = "DeepEval imports are unavailable in this environment."
            return result

        result.status = "RUNNING"
        result.started_at = datetime.now(timezone.utc).isoformat()
        started = time.monotonic()
        metric_results: list[dict[str, Any]] = []
        for case_index, case in enumerate(cases):
            prompt = case.get("input")
            actual = case.get("actual_output")
            if not isinstance(prompt, str) or not isinstance(actual, str):
                metric_results.append({
                    "case_index": case_index,
                    "metric": "validation",
                    "status": "FAILED",
                    "error": "input and actual_output must be strings",
                })
                continue
            expected = case.get("expected_output")
            if "exact_match" in metrics and not isinstance(expected, str):
                metric_results.append({
                    "case_index": case_index,
                    "metric": "exact_match",
                    "status": "FAILED",
                    "error": "expected_output is required for exact_match",
                })
                case_metrics = [name for name in metrics if name != "exact_match"]
            else:
                case_metrics = list(metrics)
            test_case = LLMTestCase(
                input=prompt,
                actual_output=actual,
                **({"expected_output": expected} if expected is not None else {}),
            )
            for metric_name in case_metrics:
                if metric_name == "answer_relevancy":
                    from deepeval.metrics import AnswerRelevancyMetric

                    metric = AnswerRelevancyMetric(
                        threshold=threshold,
                        model=judge_model,
                        include_reason=True,
                    )
                else:
                    metric = ExactMatchMetric(threshold=threshold)
                try:
                    metric.measure(test_case)
                    score = getattr(metric, "score", None)
                    metric_results.append({
                        "case_index": case_index,
                        "metric": metric_name,
                        "status": "COMPLETED",
                        "score": float(score) if score is not None else None,
                        "threshold": threshold,
                        "passed": getattr(metric, "success", None),
                        "reason": getattr(metric, "reason", None),
                    })
                except Exception as error:
                    metric_results.append({
                        "case_index": case_index,
                        "metric": metric_name,
                        "status": "FAILED",
                        "error": type(error).__name__,
                    })

        result.metrics = metric_results
        metric_statuses = [item["status"] for item in metric_results]
        result.status = (
            "FAILED" if not metric_statuses or all(s != "COMPLETED" for s in metric_statuses)
            else "COMPLETED" if all(s == "COMPLETED" for s in metric_statuses)
            else "PARTIAL"
        )
        result.duration_seconds = round(time.monotonic() - started, 4)
        result.ended_at = datetime.now(timezone.utc).isoformat()
        result.original_metadata = {
            "metric_count": len(metric_results),
            "judge_model_configured": bool(judge_model),
            "judge_calls_explicitly_allowed": allow_judge_calls,
        }
        return result
