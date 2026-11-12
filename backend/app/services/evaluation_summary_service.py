from sqlalchemy.orm import Session

from backend.app.models.evaluation_result import (
    EvaluationResult
)
from backend.app.models.test_run import TestRun


class EvaluationSummaryService:

    @staticmethod
    def summarize_run(
        test_run_id: int,
        db: Session
    ):

        results = (
            db.query(EvaluationResult)
            .filter(
                EvaluationResult.test_run_id
                ==
                test_run_id
            )
            .all()
        )

        total_cases = len(results)
        run = db.get(TestRun, test_run_id)
        completed_results = [
            result for result in results if result.status == "COMPLETED"
        ]
        failed_cases = total_cases - len(completed_results)

        if total_cases == 0:
            return {
                "test_run_id": test_run_id,
                "status": run.status if run else "UNKNOWN",
                "total_cases": 0,
                "completed_cases": 0,
                "failed_cases": 0,
                "average_score": None,
                "average_exact_match": None,
                "average_semantic_similarity": None,
                "average_hallucination_score": None,
                "hallucination_count": 0,
            }

        avg_score = (
            sum(r.score for r in completed_results)
            /
            len(completed_results)
        ) if completed_results else None

        avg_exact = (
            sum(
                r.exact_match_score
                for r in completed_results
            )
            /
            len(completed_results)
        ) if completed_results else None

        avg_semantic = (
            sum(
                r.semantic_similarity_score
                for r in completed_results
            )
            /
            len(completed_results)
        ) if completed_results else None

        avg_hallucination = (
            sum(
                r.hallucination_score
                for r in completed_results
            )
            /
            len(completed_results)
        ) if completed_results else None

        hallucination_count = sum(
            1
            for r in completed_results
            if r.hallucination_detected
        )

        pass_count = sum(
            1
            for r in completed_results
            if r.score >= 0.8
        )

        fail_count = failed_cases + len(completed_results) - pass_count

        metrics_summary = {}

        for r in completed_results:
            metric_results = getattr(r, "metric_results", {}) or {}
            for metric_name, metric_value in metric_results.items():
                stats = metrics_summary.setdefault(
                    metric_name,
                    {
                        "count": 0,
                        "min": float("inf"),
                        "max": float("-inf"),
                        "avg": 0.0
                    }
                )
                stats["count"] += 1
                stats["min"] = min(stats["min"], metric_value)
                stats["max"] = max(stats["max"], metric_value)
                stats["avg"] += metric_value

        for stats in metrics_summary.values():
            if stats["count"]:
                stats["avg"] = round(
                    stats["avg"] / stats["count"],
                    4
                )
            else:
                stats["avg"] = 0.0

        return {
            "test_run_id": test_run_id,
            "status": run.status if run else "UNKNOWN",
            "total_cases": total_cases,
            "completed_cases": len(completed_results),
            "failed_cases": failed_cases,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "average_score": round(avg_score, 4) if avg_score is not None else None,
            "average_exact_match": round(avg_exact, 4) if avg_exact is not None else None,
            "average_semantic_similarity": round(
                avg_semantic,
                4
            ) if avg_semantic is not None else None,
            "average_hallucination_score": round(
                avg_hallucination,
                4
            ) if avg_hallucination is not None else None,
            "hallucination_count": hallucination_count,
            "metrics_summary": metrics_summary
        }
