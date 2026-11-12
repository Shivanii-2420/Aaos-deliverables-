# Database

AAOS uses SQLAlchemy ORM models and a synchronous SQLAlchemy session. SQLite is the local default; `DATABASE_URL` can point at another supported SQLAlchemy database. The local mock workflow does not require Redis.

## Current entities

The ORM defines agents, agent versions, test runs, evaluation cases/results, traces, attack results, risk scores, findings, certificates, evaluation datasets, adaptive assurance runs/evidence/decisions, and external tool execution records. Credentials are loaded from environment configuration rather than represented as provider records in the database. There are no user-account tables.

## Initialization and migration

From the repository root, set `DATABASE_URL` to the intended local database and run:

```powershell
.\.venv-aaos\Scripts\python.exe scripts\init_db.py
.\.venv-aaos\Scripts\python.exe -m alembic upgrade head
```

Initialization creates missing tables and does not drop existing tables. Alembic adds dataset associations and snapshots, assurance tables, and missing legacy case/run columns and indexes. The migration test upgrades a legacy SQLite database twice and confirms the pre-existing case is preserved. The current migration intentionally has a non-destructive downgrade. This is not yet a full historical migration chain for every table: review the target database and make a backup before applying schema changes.

Dataset-bound runs record the dataset version, a SHA-256 hash, selected case IDs, and a copy of the case content used for evaluation. Later dataset edits do not change the inputs of a new-format run. The additive `20261113_01` migration adds the nullable JSON snapshot column; historical dataset runs have no backfilled content and retain the prior ID-based execution behavior. Non-dataset runs retain compatibility with run-scoped cases and the legacy unscoped-case fallback.

Runs can be evaluated once. A repeated request for a running or terminal run is rejected with HTTP 409; create a new run for another evaluation.

Do not use `scripts\create_db.py` for routine initialization; it includes a destructive reset path.
