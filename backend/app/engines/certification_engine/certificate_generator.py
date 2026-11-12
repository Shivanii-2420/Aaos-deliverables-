import uuid


class CertificateGenerator:

    @staticmethod
    def generate(score: float):

        status = (
            "PASSED"
            if score >= 0.70
            else "FAILED"
        )

        return {
            "certificate_no": str(uuid.uuid4()),
            "status": status,
            "score": score
        }