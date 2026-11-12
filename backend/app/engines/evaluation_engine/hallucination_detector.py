class HallucinationDetector:
    """Lexical overlap heuristic, not a factuality or hallucination verifier."""

    @staticmethod
    def detect(
        expected: str,
        actual: str
    ):

        expected_words = set(
            expected.lower().split()
        )

        actual_words = set(
            actual.lower().split()
        )

        overlap = len(
            expected_words.intersection(
                actual_words
            )
        )

        hallucination_score = (
            overlap /
            max(len(expected_words), 1)
        )

        hallucination = (
            hallucination_score < 0.30
        )

        return {
            "hallucination": hallucination,
            "score": round(
                hallucination_score,
                4
            )
        }