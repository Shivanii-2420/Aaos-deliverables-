from difflib import SequenceMatcher

from backend.app.engines.evaluation_engine.metrics.base_metric import (
    BaseMetric
)


class SimilarityMetric(BaseMetric):

    name = "similarity"
    description = (
        "Character-sequence similarity from difflib.SequenceMatcher; "
        "not semantic or embedding similarity."
    )
    score_range = (0.0, 1.0)

    def evaluate(
        self,
        expected: str,
        actual: str
    ) -> float:

        return round(
            SequenceMatcher(
                None,
                expected.lower(),
                actual.lower()
            ).ratio(),
            2
        )
