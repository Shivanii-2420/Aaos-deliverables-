from backend.app.engines.evaluation_engine.registry import get_metrics
from backend.app.engines.evaluation_engine.hallucination_detector import (
    HallucinationDetector,
)


class Evaluator:

    @staticmethod
    def evaluate(
        expected: str,
        actual: str
    ):

        metric_results = {}
        metrics = get_metrics()

        for metric in metrics:
            metric_results[metric.name] = metric.evaluate(
                expected,
                actual
            )

        exact_score = metric_results.get("exact_match", 0.0)
        semantic_score = metric_results.get("similarity", 0.0)

        final_score = (
            exact_score * 0.3
            +
            semantic_score * 0.7
        )

        hallucination_obj = HallucinationDetector.detect(
            expected,
            actual
        )

        return {
            "metric_results": metric_results,
            "exact_match": exact_score,
            "semantic_similarity": semantic_score,
            "hallucination_detected": hallucination_obj["hallucination"],
            "hallucination_score": hallucination_obj["score"],
            "score": round(final_score, 4)
        }
