# Testing

The test suite uses Python's built-in `unittest`, FastAPI's TestClient, and an isolated in-memory SQLite database. It patches no external model for the end-to-end route: the app is configured to use its deterministic mock provider.

Run from the repository root:

```powershell
$env:DATABASE_URL = "sqlite://"
$env:REDIS_URL = ""
$env:DEFAULT_LLM_PROVIDER = "mock"
.\.venv-aaos\Scripts\python.exe -m unittest discover -s tests -v
```

The suite covers metric/risk behavior; health, UI, and local API-token boundaries; evaluation result retrieval; dataset run snapshots; migration preservation/idempotency; EGAA gap calculation, selection, and persistence; mocked Garak/DeepEval adapter behavior; and shared LiteLLM timeout, sanitization, and bounded-retry behavior. Tool execution tests use mocks: they do not prove that the external packages are installed or that a live provider/tool works.

The browser UI has also been smoke-tested against an isolated SQLite database: mock evaluation, dashboard update, EGAA run, stored result inspection, and provider/tool status display all completed. No browser automation test suite is committed. No real provider, paid judge, or external target was called. Tests do not establish formal security assurance, PostgreSQL behavior, or production readiness.
