# AAOS — Advanced AI Operations Suite

AAOS is a local-first prototype for evaluating text responses from configured AI providers. It stores evaluation runs and traces, calculates basic response scores and risk records, and can produce a PDF summary. Its default provider is a deterministic mock, so the local demonstration does not require credentials or call an external model.

## Final review deliverables

The three canonical Markdown sources and their review-ready PDF exports are:

| Category | Authoritative Markdown | PDF export |
|---|---|---|
| POV — Adaptive Assurance | [POV_ADAPTIVE_ASSURANCE.md](docs/POV_ADAPTIVE_ASSURANCE.md) | [POV_ADAPTIVE_ASSURANCE.pdf](docs/final_review/POV_ADAPTIVE_ASSURANCE.pdf) |
| POV — Provider Disagreement | [POV_PROVIDER_DISAGREEMENT.md](docs/POV_PROVIDER_DISAGREEMENT.md) | [POV_PROVIDER_DISAGREEMENT.pdf](docs/final_review/POV_PROVIDER_DISAGREEMENT.pdf) |
| EGAA Innovation / IP Note | [INNOVATION_NOTE_EGAA.md](docs/INNOVATION_NOTE_EGAA.md) | [INNOVATION_NOTE_EGAA.pdf](docs/final_review/INNOVATION_NOTE_EGAA.pdf) |

These are internal review drafts. The assurance-tool adapters have not been
executed against installed Garak or DeepEval packages; the EGAA benchmark is
synthetic; and no external publication, patentability, or client acceptance is
established. See [assurance-tool limits](docs/ASSURANCE_TOOLS.md),
[known limitations](docs/KNOWN_LIMITATIONS.md), and the [implementation status
report](docs/FINAL_AUDIT_REPORT.md).

## Local Windows quick start

Use Python 3.10 or newer. From the repository root in VS Code PowerShell:

```powershell
py -3.13 -m venv .venv-aaos
.\.venv-aaos\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:DATABASE_URL = "sqlite:///./aaos_local.db"
$env:REDIS_URL = ""
$env:DEFAULT_LLM_PROVIDER = "mock"
.\.venv-aaos\Scripts\python.exe scripts\init_db.py
.\.venv-aaos\Scripts\python.exe -m alembic upgrade head
.\.venv-aaos\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000/ui` for the demo or `http://127.0.0.1:8000/docs` for the API. Press Ctrl+C in the terminal to stop the server. `scripts\init_db.py` creates missing tables and does not drop existing tables. The demo creates records in `aaos_local.db` and a PDF under `reports\`; it does not call a live provider when the default `mock` mode is selected.

For a disposable demonstration database instead of `aaos_local.db`, use a fresh PowerShell terminal:

```powershell
$demoDb = Join-Path $env:TEMP ("aaos-demo-" + [guid]::NewGuid().ToString("N") + ".db")
$env:DATABASE_URL = "sqlite:///" + ($demoDb -replace '\\', '/')
$env:REDIS_URL = ""
$env:DEFAULT_LLM_PROVIDER = "mock"
.\.venv-aaos\Scripts\python.exe scripts\init_db.py
.\.venv-aaos\Scripts\python.exe -m alembic upgrade head
.\.venv-aaos\Scripts\python.exe -m uvicorn backend.main:app --reload
```

In the UI, optionally select **Create a dataset snapshot** before running the evaluation. Inspect the selected run to see its results, traces, built-in mock probes, EGAA history, optional-tool status/results, and any internal unsigned assessment. PDF output is written to `reports\`; existing files are not overwritten.

The **Hallucination evaluation** panel separately accepts a prompt, response, and optional reference documents. It runs offline with no model calls. Its category coverage and scoring limitations are described in [the evaluation-engine notes](docs/EVALUATION_ENGINE.md); existing stored-run scores and reports are unchanged.

To run tests in a separate process:

```powershell
$env:DATABASE_URL = "sqlite://"
$env:REDIS_URL = ""
$env:DEFAULT_LLM_PROVIDER = "mock"
.\.venv-aaos\Scripts\python.exe -m unittest discover -s tests -v
```

Provider errors are persisted as failed evaluation cases with redacted error
messages. Runs with any failed case or no evaluable cases finish as `FAILED`;
only fully completed runs receive an internal, unsigned assessment. Assessments
are created from persisted results for the requested `test_run_id`; caller
supplied scores are not accepted. The `POST /certificates` body is
`{"test_run_id": 1}`.

For local API protection, set `API_TOKEN` to a random value of at least 24 characters. If unset, protected APIs only accept loopback clients. Do not expose this prototype to an untrusted network.

See [installation and run notes](docs/INSTALLATION.md), [architecture](docs/ARCHITECTURE.md), [backend](docs/BACKEND.md), [frontend](docs/FRONTEND.md), [database](docs/DATABASE.md), [API reference](docs/API_REFERENCE.md), [evaluation engine](docs/EVALUATION_ENGINE.md), [security testing](docs/SECURITY_TESTING.md), [testing](docs/TESTING.md), [assurance tools](docs/ASSURANCE_TOOLS.md), the [EGAA POV](docs/POV_ADAPTIVE_ASSURANCE.md), the [provider-disagreement POV](docs/POV_PROVIDER_DISAGREEMENT.md), the [innovation note](docs/INNOVATION_NOTE_EGAA.md), [known limitations](docs/KNOWN_LIMITATIONS.md), and the [final status report](docs/FINAL_AUDIT_REPORT.md).

## Current scope

The evaluator uses exact match and character-sequence similarity. A lexical overlap heuristic is labelled as a heuristic, not a factuality check. The built-in attack list has only three static probes and a keyword detector. Optional Garak and DeepEval adapters expose status, execution and persisted results; neither optional package is installed here, so neither has been executed. PyRIT and Promptfoo are not integrated. Dataset snapshots, additive Alembic migrations, local API-token protection, and adaptive evidence-gap-guided assurance (EGAA) are available. The benchmark is synthetic; AAOS-generated assessment records are internal, unsigned evidence and are not external safety certification.

New dataset-backed runs persist both the selected case content and its hash, so later dataset edits do not change their inputs. Evaluation runs are single-use: rerun attempts receive HTTP 409; create a new run to repeat an evaluation without appending duplicate results or assessments.

The two POVs and the EGAA innovation note are drafts for internal review:
[adaptive assurance](docs/POV_ADAPTIVE_ASSURANCE.md),
[provider disagreement](docs/POV_PROVIDER_DISAGREEMENT.md), and
[EGAA innovation note](docs/INNOVATION_NOTE_EGAA.md). They are not evidence of
external publication or patentability. See the [current implementation report](docs/FINAL_AUDIT_REPORT.md)
for verified test results and limitations.
