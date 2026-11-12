from backend.app.engines.risk_engine.policies import RiskPolicy
from backend.app.engines.risk_engine.scorer import RiskScorer


class RiskCalculator:

    @staticmethod
    def calculate(avg_score: float, hallucinations: int = 0, attack_successes: int = 0):

        policy = RiskPolicy.evaluate(avg_score, hallucinations, attack_successes)

        security_score = RiskScorer.adjust_score(
            avg_score,
            policy["modifier"]
        )
        reliability_score = RiskScorer.adjust_score(
            avg_score,
            policy["modifier"]
        )

        overall_score = (
            security_score + reliability_score
        ) / 2

        return {
            "security_score": security_score,
            "reliability_score": reliability_score,
            "overall_score": overall_score,
            "severity": policy["severity"]
        }