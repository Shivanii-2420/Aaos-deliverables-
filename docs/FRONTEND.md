# Frontend

The frontend is a small, same-origin HTML/CSS/JavaScript demo under `frontend/`, served by FastAPI at `/ui` and `/static`. It calls the local API for agent/version/run/case creation, evaluation, dashboard summaries, attack probes, and PDF reports. Evaluations can be run with a run-scoped case or by creating a dataset, adding a case, and creating a run against that dataset version.

The dashboard displays database-backed run counts, recent runs, and average scores. Run history loads persisted case outcomes, traces, built-in probe results, run-specific internal assessments, and optional tool execution history. The UI also exposes EGAA evidence selection, optional tool availability, provider configuration, and PDF reports. The evaluation form and mock probes are enabled only when the health response says the configured provider mode is `mock`. Protected APIs also enforce the server-side token/loopback rule; UI gating is not a substitute for server-side authorization.

The UI is not a full provider-management or analytics application. Provider status indicates configuration, not a live health check. Optional tool controls remain disabled when packages are absent. It has no committed frontend unit-test framework; validate UI changes with a browser smoke test against an isolated SQLite database.
