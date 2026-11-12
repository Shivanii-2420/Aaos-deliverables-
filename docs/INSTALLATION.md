# Local installation and operation

## Prerequisites

- Windows 10/11 and VS Code with the Python extension.
- Python 3.10 or newer. The existing project does not pin a supported Python range; use a maintained Python version compatible with the pinned packages.
- Network access only to install Python dependencies.

## Install

Open the AAOS repository root in VS Code, choose **Terminal → New Terminal**, and run:

```powershell
py -0p
py -3.13 -m venv .venv-aaos
.\.venv-aaos\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Package installation requires network access. No model is downloaded by the local mock demonstration. If Python 3.13 is unavailable, substitute an installed Python version of 3.10 or newer that is compatible with the pinned dependencies.

## Safe local configuration

In the same PowerShell terminal:

```powershell
$env:DATABASE_URL = "sqlite:///./aaos_local.db"
$env:REDIS_URL = ""
$env:DEFAULT_LLM_PROVIDER = "mock"
```

These settings point the demo at a separate local SQLite file and force the deterministic mock provider. Do not copy production database URLs or credentials into the terminal, screenshots, or source control. [backend/.env.example](../backend/.env.example) contains placeholders only; do not overwrite an existing `backend/.env`.

Create missing tables without dropping data:

```powershell
.\.venv-aaos\Scripts\python.exe scripts\init_db.py
.\.venv-aaos\Scripts\python.exe -m alembic upgrade head
```

These commands use the configured database. Alembic applies additive dataset/assurance schema changes and preserves legacy case data. Verify `DATABASE_URL` is set to the intended local database and back up existing data before migration. Do not use `scripts\create_db.py` for ordinary setup: it calls a reset function that drops tables.

## Start and use

```powershell
.\.venv-aaos\Scripts\python.exe -m uvicorn backend.main:app --reload
```

- Web demonstration: `http://127.0.0.1:8000/ui`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/health`

The UI creates agent/version/run/case records, evaluates them with the mock provider, and can request a PDF. Those actions write to the configured database and reports directory. Stop the server with Ctrl+C.

If `API_TOKEN` is configured, enter its Bearer token in the UI when prompted; it is retained only for the current browser tab. If no token is configured, protected APIs are restricted to loopback clients. This local guard is not production authentication.

## Optional live-provider mode

Live provider calls can incur cost and send evaluation prompts to an external service. Set the desired `DEFAULT_LLM_PROVIDER` (`azure`, `claude`, or `gemini`) and the corresponding credentials/configuration listed in [backend/.env.example](../backend/.env.example) only after confirming authorization, billing, and data-handling requirements. Live calls have not been verified as part of this implementation.
