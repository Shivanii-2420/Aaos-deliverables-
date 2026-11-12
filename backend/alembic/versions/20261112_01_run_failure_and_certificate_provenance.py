"""Persist evaluation failure details and certificate run provenance.

Revision ID: 20261112_01
Revises: 20261111_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20261112_01"
down_revision = "20261111_01"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table):
        return set()
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    if "status" not in _columns("evaluation_results"):
        with op.batch_alter_table("evaluation_results") as batch:
            batch.add_column(sa.Column(
                "status",
                sa.String(length=30),
                nullable=False,
                server_default="COMPLETED",
            ))
    result_columns = _columns("evaluation_results")
    missing_result_columns = [
        column for column in (
            sa.Column("error_type", sa.String(length=100), nullable=True),
            sa.Column("error_message", sa.String(length=255), nullable=True),
        )
        if column.name not in result_columns
    ]
    if missing_result_columns:
        with op.batch_alter_table("evaluation_results") as batch:
            for column in missing_result_columns:
                batch.add_column(column)

    if "test_run_id" not in _columns("certificates"):
        with op.batch_alter_table("certificates") as batch:
            batch.add_column(sa.Column("test_run_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(
                "fk_certificates_test_run_id",
                "test_runs",
                ["test_run_id"],
                ["id"],
            )
    if "assessment_type" not in _columns("certificates"):
        with op.batch_alter_table("certificates") as batch:
            batch.add_column(sa.Column(
                "assessment_type",
                sa.String(length=50),
                nullable=False,
                server_default="INTERNAL_UNSIGNED_ASSESSMENT",
            ))
    indexes = {
        item["name"] for item in sa.inspect(op.get_bind()).get_indexes("certificates")
    }
    if "ix_certificates_test_run_id" not in indexes:
        op.create_index(
            "ix_certificates_test_run_id",
            "certificates",
            ["test_run_id"],
        )


def downgrade() -> None:
    # Preserve assessment and evaluation history during automated downgrades.
    pass
