from backend.app.engines.evaluation_engine.metrics.exact_match_metric import (
    ExactMatchMetric
)

from backend.app.engines.evaluation_engine.metrics.similarity_metric import (
    SimilarityMetric
)


def get_metrics():

    return [

        ExactMatchMetric(),

        SimilarityMetric()
    ]
