from uuid import uuid4


class CertificateGenerator:

    @staticmethod
    def generate_no():

        return (
            "AAOS-"
            +
            str(uuid4())[:8]
        )