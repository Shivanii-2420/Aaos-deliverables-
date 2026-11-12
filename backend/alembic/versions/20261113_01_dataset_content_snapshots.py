"""Persist dataset case content with each dataset-backed run."""
from alembic import op
import sqlalchemy as sa

revision = "20261113_01"
down_revision = "20261112_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("test_runs"):
        return
    columns = {column["name"] for column in inspector.get_columns("test_runs")}
    if "dataset_snapshot" not in columns:
        with op.batch_alter_table("test_runs") as batch:
            batch.add_column(sa.Column("dataset_snapshot", sa.JSON(), nullable=True))


def downgrade() -> None:
    # Keep stored evaluation evidence intact during automated downgrades.
    pass
