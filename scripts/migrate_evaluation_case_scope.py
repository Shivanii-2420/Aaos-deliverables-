from pathlib import Path
import sys

from sqlalchemy import inspect, text

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from backend.app.database.init_db import create_tables
from backend.app.database.session import engine


def migrate_evaluation_case_scope(database_engine):
    columns = {
        column["name"]
        for column in inspect(database_engine).get_columns("evaluation_cases")
    }

    if "test_run_id" not in columns:
        with database_engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE evaluation_cases "
                "ADD COLUMN test_run_id INTEGER "
                "REFERENCES test_runs(id)"
            ))

    indexes = {
        index["name"]
        for index in inspect(database_engine).get_indexes("evaluation_cases")
    }
    if "ix_evaluation_cases_test_run_id" not in indexes:
        with database_engine.begin() as connection:
            connection.execute(text(
                "CREATE INDEX ix_evaluation_cases_test_run_id "
                "ON evaluation_cases (test_run_id)"
            ))


if __name__ == "__main__":
    create_tables()
    migrate_evaluation_case_scope(engine)
    print("Evaluation case run-scope migration applied; existing cases were preserved.")
