from backend.app.engines.evaluation_engine.metrics.base_metric import (
    BaseMetric
)


class ExactMatchMetric(BaseMetric):

    name = "exact_match"
    description = "Case-insensitive exact match after trimming whitespace."
    score_range = (0.0, 1.0)

    def evaluate(
        self,
        expected: str,
        actual: str
    ) -> float:

        if (
            expected.strip().lower()
            ==
            actual.strip().lower()
        ):
            return 1.0

        return 0.0
