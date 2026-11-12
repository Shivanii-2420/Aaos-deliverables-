from sqlalchemy.orm import Session
from backend.app.models.test_run import TestRun
from backend.app.models.certificate import Certificate
from backend.app.services.certificate_generator import CertificateGenerator
from backend.app.engines.certification_engine.evidence_builder import (
    EvidenceBuilder
)


class CertificateService:

    @staticmethod
    def create_certificate(test_run_id: int, db: Session):
        run = db.get(TestRun, test_run_id)
        if run is None:
            raise LookupError(f"Test run {test_run_id} was not found")
        if run.status != "COMPLETED":
            raise ValueError("Only completed test runs can be assessed")

        evidence, score = EvidenceBuilder.build(test_run_id=test_run_id, db=db)
        cert_no = CertificateGenerator.generate_no()
        status = "PASSED" if score >= 0.70 else "FAILED"

        certificate = Certificate(
            agent_version_id=run.agent_version_id,
            test_run_id=run.id,
            certificate_no=cert_no,
            status=status,
            assessment_type="INTERNAL_UNSIGNED_ASSESSMENT",
            score=score,
            evidence=evidence
        )

        db.add(certificate)
        db.commit()
        db.refresh(certificate)

        return certificate

    @staticmethod
    def get_certificates(db: Session):
        """
        Retrieve all certificates.
        """
        return db.query(Certificate).all()

    @staticmethod
    def get_certificate(cert_id: int, db: Session):
        """
        Retrieve a single certificate by ID.
        """
        return (
            db.query(Certificate)
            .filter(Certificate.id == cert_id)
            .first()
        )
