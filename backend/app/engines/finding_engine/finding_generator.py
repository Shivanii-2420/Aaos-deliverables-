class FindingGenerator:

    @staticmethod
    def generate(score: float):

        if score < 0.30:
            return {
                "severity": "HIGH",
                "finding": "Response quality is poor"
            }

        if score < 0.70:
            return {
                "severity": "MEDIUM",
                "finding": (
                    "Response quality is acceptable "
                    "but needs improvement"
                )
            }

        return {
            "severity": "LOW",
            "finding": "Response quality is good"
        }