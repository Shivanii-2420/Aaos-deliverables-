"""Add run-scoped assurance storage and dataset snapshots safely.

Revision ID: 20261111_01
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "20261111_01"
down_revision = None
branch_labels = None
depends_on = None


def _column_names(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table(table):
        return set()
    return {column["name"] for column in inspector.get_columns(table)}


def _ensure_columns_and_foreign_keys(
    table: str,
    columns: list[sa.Column],
    foreign_keys: list[tuple[str, str, str, str]],
) -> None:
    inspector = sa.inspect(op.get_bind())
    names = _column_names(table)
    missing_columns = [column for column in columns if column.name not in names]
    existing_foreign_keys = {
        (
            tuple(item["constrained_columns"]),
            item["referred_table"],
            tuple(item["referred_columns"]),
        )
        for item in inspector.get_foreign_keys(table)
    }
    missing_foreign_keys = [
        item for item in foreign_keys
        if ((item[0],), item[1], (item[2],)) not in existing_foreign_keys
    ]
    if not missing_columns and not missing_foreign_keys:
        return
    with op.batch_alter_table(table, recreate="always") as batch:
        for column in missing_columns:
            batch.add_column(column)
        for name, target_table, local_column, target_column in missing_foreign_keys:
            batch.create_foreign_key(
                name,
                target_table,
                [local_column],
                [target_column],
            )


def upgrade() -> None:
    from backend.app import models  # noqa: F401
    from backend.app.database.base import Base

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    _ensure_columns_and_foreign_keys(
        "evaluation_cases",
        [
            sa.Column("test_run_id", sa.Integer(), nullable=True),
            sa.Column("dataset_id", sa.Integer(), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
        ],
        [
            ("fk_evaluation_cases_test_run", "test_runs", "test_run_id", "id"),
            ("fk_evaluation_cases_dataset", "evaluation_datasets", "dataset_id", "id"),
        ],
    )
    _ensure_columns_and_foreign_keys(
        "test_runs",
        [
            sa.Column("dataset_id", sa.Integer(), nullable=True),
            sa.Column("dataset_version", sa.Integer(), nullable=True),
            sa.Column("dataset_snapshot_hash", sa.String(length=64), nullable=True),
            sa.Column("dataset_case_ids", sa.JSON(), nullable=True),
        ],
        [
            ("fk_test_runs_dataset", "evaluation_datasets", "dataset_id", "id"),
        ],
    )

    inspector = sa.inspect(bind)
    indexes = {
        index["name"] for index in inspector.get_indexes("evaluation_cases")
    }
    if "ix_evaluation_cases_test_run_id" not in indexes:
        op.create_index(
            "ix_evaluation_cases_test_run_id",
            "evaluation_cases",
            ["test_run_id"],
        )
    if "ix_evaluation_cases_dataset_id" not in indexes:
        op.create_index(
            "ix_evaluation_cases_dataset_id",
            "evaluation_cases",
            ["dataset_id"],
        )
    run_indexes = {index["name"] for index in inspector.get_indexes("test_runs")}
    if "ix_test_runs_dataset_id" not in run_indexes:
        op.create_index(
            "ix_test_runs_dataset_id",
            "test_runs",
            ["dataset_id"],
        )

    bind.execute(sa.text(
        "UPDATE evaluation_cases SET tags = '[]' WHERE tags IS NULL"
    ))
    bind.execute(sa.text(
        'UPDATE evaluation_cases SET "metadata" = \'{}\' '
        'WHERE "metadata" IS NULL'
    ))


def downgrade() -> None:
    # This migration is intentionally non-destructive; existing evaluation
    # evidence and user datasets must not be dropped by an automated downgrade.
    pass
