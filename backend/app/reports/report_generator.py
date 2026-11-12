from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from pathlib import Path
from html import escape
from uuid import uuid4


class ReportGenerator:

    REPORTS_DIRECTORY = (
        Path(__file__).resolve().parents[3] / "reports"
    )

    @staticmethod
    def generate(
        filename: str,
        data: dict
    ):

        safe_filename = Path(filename).name
        if safe_filename != filename or not safe_filename.lower().endswith(".pdf"):
            raise ValueError("Report filename must be a plain PDF filename")

        ReportGenerator.REPORTS_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True
        )
        pdf_path = ReportGenerator.REPORTS_DIRECTORY / safe_filename
        if pdf_path.exists():
            pdf_path = pdf_path.with_name(
                f"{pdf_path.stem}_{uuid4().hex[:8]}{pdf_path.suffix}"
            )

        doc = SimpleDocTemplate(
            str(pdf_path)
        )

        styles = (
            getSampleStyleSheet()
        )

        content = []

        content.append(
            Paragraph(
                "AAOS Assurance Report",
                styles["Title"]
            )
        )

        content.append(
            Spacer(1, 20)
        )

        for key, value in data.items():

            content.append(
                Paragraph(
                    f"<b>{escape(str(key))}</b>: {escape(str(value))}",
                    styles["BodyText"]
                )
            )

        doc.build(content)

        return str(pdf_path)