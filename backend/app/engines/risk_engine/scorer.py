class RiskScorer:

    @staticmethod
    def adjust_score(base_score: float, modifier: float) -> float:
        adjusted = base_score + modifier
        return max(0.0, min(adjusted, 1.0))
