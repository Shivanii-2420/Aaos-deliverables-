from sqlalchemy.orm import Session

from backend.app.models.test_run import TestRun
from backend.app.models.risk_score import RiskScore
from backend.app.models.finding import Finding
from backend.app.models.evaluation_result import EvaluationResult
from backend.app.models.execution_trace import ExecutionTrace
from backend.app.models.attack_result import AttackResult
from backend.app.models.assurance import (
    AssuranceRunRecord,
    ToolExecutionRecord,
)

from backend.app.reports.report_generator import ReportGenerator


class ReportService:

    @staticmethod
    def generate(
        test_run_id: int,
        db: Session
    ):
        # Load run
        run = (
            db.query(TestRun)
            .filter(TestRun.id == test_run_id)
            .first()
        )
        if run is None:
            raise LookupError(f"Test run {test_run_id} was not found")

        # Load risk scores
        risk = (
            db.query(RiskScore)
            .filter(RiskScore.test_run_id == test_run_id)
            .first()
        )

        # Load findings
        findings = (
            db.query(Finding)
            .filter(Finding.test_run_id == test_run_id)
            .all()
        )

        # Load evaluation results
        results = (
            db.query(EvaluationResult)
            .filter(EvaluationResult.test_run_id == test_run_id)
            .all()
        )

        # Calculate averages
        avg_exact = 0
        avg_semantic = 0
        avg_hallucination = 0

        if results:
            completed_results = [
                result for result in results if result.status == "COMPLETED"
            ]
        else:
            completed_results = []

        if completed_results:
            avg_exact = (
                sum(r.exact_match_score for r in completed_results)
                / len(completed_results)
            )
            avg_semantic = (
                sum(r.semantic_similarity_score for r in completed_results)
                / len(completed_results)
            )
            avg_hallucination = (
                sum(r.hallucination_score for r in completed_results)
                / len(completed_results)
            )

        trace_count = (
            db.query(ExecutionTrace)
            .filter(ExecutionTrace.test_run_id == test_run_id)
            .count()
        )

        attack_count = (
            db.query(AttackResult)
            .filter(AttackResult.test_run_id == test_run_id)
            .count()
        )
        assurance_runs = (
            db.query(AssuranceRunRecord)
            .filter(AssuranceRunRecord.test_run_id == test_run_id)
            .order_by(AssuranceRunRecord.id)
            .all()
        )
        tool_runs = (
            db.query(ToolExecutionRecord)
            .filter(ToolExecutionRecord.test_run_id == test_run_id)
            .order_by(ToolExecutionRecord.id)
            .all()
        )

        # Build report payload
        report_data = {
            "Run ID": run.id,
            "Run Status": run.status,
            "Agent Version": run.agent_version_id,

            "Security Score": risk.security_score if risk else "N/A",
            "Reliability Score": risk.reliability_score if risk else "N/A",
            "Overall Score": risk.overall_score if risk else "N/A",

            "Findings Count": len(findings),
            "Trace Count": trace_count,
            "Attack Result Count": attack_count,

            "Average Exact Match": (
                round(avg_exact, 4) if completed_results else "N/A"
            ),
            "Average Semantic Similarity": (
                round(avg_semantic, 4) if completed_results else "N/A"
            ),
            "Average Hallucination Score": (
                round(avg_hallucination, 4) if completed_results else "N/A"
            )
        }
        report_data["Completed Evaluation Cases"] = len(completed_results)
        report_data["Failed Evaluation Cases"] = len(results) - len(completed_results)

        report_data["Adaptive Assurance Runs"] = len(assurance_runs)
        for index, assurance in enumerate(assurance_runs, start=1):
            report_data[f"EGAA Run {index} Status"] = assurance.status
            report_data[f"EGAA Run {index} Stopping Reason"] = (
                assurance.summary.get("stopped_reason", "unknown")
            )
            report_data[f"EGAA Run {index} Selected Tests"] = ", ".join(
                str(step.get("decision", {}).get("selected_test", "unknown"))
                for step in assurance.summary.get("selection_history", [])
            ) or "None"
            report_data[f"EGAA Run {index} Unresolved Risks"] = ", ".join(
                str(risk.get("risk_id", "unknown"))
                for risk in assurance.summary.get("unresolved_risks", [])
            ) or "None"

        report_data["External Assurance Tool Executions"] = len(tool_runs)
        for index, tool_run in enumerate(tool_runs, start=1):
            report_data[f"Tool {index}"] = (
                f"{tool_run.tool} {tool_run.status} "
                f"(version: {tool_run.version or 'unavailable'})"
            )
            report_data[f"Tool {index} Findings"] = len(tool_run.findings or [])
            report_data[f"Tool {index} Metrics"] = len(tool_run.metrics or [])
            if tool_run.error:
                report_data[f"Tool {index} Note"] = tool_run.error

        # Add findings content
        for idx, finding in enumerate(findings, start=1):
            report_data[f"Finding {idx}"] = (
                f"{finding.severity} - {finding.finding}"
            )

        report_data["Trace Count"] = trace_count
        report_data["Attack Result Count"] = attack_count

        # Generate PDF report
        return ReportGenerator.generate(
            f"report_{test_run_id}.pdf",
            report_data
        )
