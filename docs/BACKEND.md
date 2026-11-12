# Backend

## Runtime

The backend is a synchronous FastAPI application created in `backend/main.py`. SQLAlchemy sessions are supplied through `get_db`; the provider router selects the configured mock, Azure OpenAI, Claude, or Gemini adapter.

The app exposes its OpenAPI document at `/docs`, a basic liveness response at `/health`, and the same-origin demo at `/ui`. `/health` reports configured provider mode; it is not a dependency or provider-health check. Protected APIs require `API_TOKEN` as a Bearer credential when configured, and otherwise accept only loopback clients.

## Evaluation execution

Create an agent, version, run, and one or more evaluation cases, then call `POST /evaluation-execution/{test_run_id}`. Cases associated with the run are evaluated first. For compatibility with older clients, if a run has no scoped cases, unscoped legacy cases are evaluated. A case that names an unknown run is rejected with HTTP 404.

Each case produces a provider response, trace and result; the service then writes a risk record, finding, and certificate evidence. Dataset-bound runs use a frozen case-ID snapshot and record the dataset version/hash. A failed provider call is recorded as a failed response path, but the workflow and resulting risk evidence should not be treated as an independent safety judgment.

## Adaptive assurance and optional tool adapters

`POST /assurance/runs/{test_run_id}` runs the evidence-gap-guided assurance loop only when the configured provider is `mock`. It reweights stored evidence for confidence, freshness, and evidence mode; selects from a deterministic catalog using risk-weighted expected gap reduction per cost; and persists its decisions and evidence. The internal benchmark uses synthetic scenarios only.

Garak and DeepEval are optional tools. The Garak subprocess runner uses an allowlist, explicit authorization, and a timeout; DeepEval's exact-match metric does not need an LLM, while answer relevancy requires explicit judge configuration and external-call confirmation. The packages are not installed and actual tool runs have not been verified here.

## Configuration and limitations

Settings are loaded from environment variables and optionally `backend/.env`. Shared provider calls use a 30-second timeout and one bounded retry for connection/service-unavailable exceptions. Do not enable live provider mode until billing, data handling, and credentials are explicitly reviewed. Provider availability is configuration-only; live adapters have not been exercised. The API token/loopback control is not production identity or authorization; do not expose this service to an untrusted network.

Run the API from the project root:

```powershell
.\.venv-aaos\Scripts\python.exe -m uvicorn backend.main:app --reload
```
