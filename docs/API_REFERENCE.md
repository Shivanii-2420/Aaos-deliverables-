# API reference

The authoritative interactive OpenAPI specification is served at `/docs`. The current routes include:

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Application name, version, and status |
| GET | `/health` | Liveness and configured provider mode |
| POST, GET | `/agents` | Create/list AI agents |
| POST, GET | `/agents/{agent_id}/versions` | Create/list agent versions |
| POST, GET | `/versions/{version_id}/runs` | Create/list test runs |
| POST, GET | `/evaluation-cases` | Create/list cases; optional `test_run_id` on create and list |
| POST | `/evaluation-execution/{test_run_id}` | Execute a new evaluation run once; repeated/running/terminal runs return HTTP 409 |
| POST | `/evaluation/run/{test_run_id}` | Alternate single-use execution route |
| GET | `/evaluation/run/{test_run_id}/summary` | Summarize a run |
| POST | `/evaluation/hallucination` | Offline claim grounding evaluation with optional reference context |
| GET | `/evaluation-results?test_run_id={id}` | List up to 500 latest results, optionally scoped to a run, with prompts and measured outputs |
| POST, GET | `/datasets` | Create/list datasets with case count and content hash |
| GET | `/datasets/{dataset_id}` | Get a dataset and its cases |
| POST | `/datasets/{dataset_id}/cases` | Add a case to a dataset |
| POST | `/datasets/{dataset_id}/versions/{version_id}/runs` | Create a run with frozen dataset version/hash/case IDs and case content |
| POST, GET | `/attacks/run`, `/attacks` | Execute built-in probes/list attack results |
| GET | `/llm/providers` | Provider configuration availability |
| GET | `/llm/providers/available` | List configured providers |
| GET | `/llm/graph` | Basic provider availability graph |
| POST | `/llm/select?prompt=...` | Select a configured provider |
| GET, POST | `/traces` | List/create traces |
| GET, POST | `/risk-scores` | List/create risk scores |
| GET, POST | `/findings` | List/create findings |
| GET, POST | `/certificates` | List/create internal unsigned assessment evidence |
| POST | `/reports/{test_run_id}` | Generate and return a PDF report |
| GET | `/dashboard/summary` | Dashboard counts and recent runs |
| GET | `/system-summary` | Aggregate system counts |
| GET | `/run-summary/{test_run_id}` | Run result summary |
| GET | `/agent-performance/{agent_id}` | Agent performance summary |
| GET | `/assurance/taxonomy`, `/assurance/tests` | List risk dimensions and test catalog |
| GET | `/assurance/benchmark` | Run deterministic synthetic benchmark fixtures |
| POST | `/assurance/runs/{test_run_id}` | Execute bounded mock-mode EGAA and persist evidence/decisions |
| GET | `/assurance/runs/{assurance_run_id}` | Retrieve a stored assurance run |
| GET | `/assurance/runs/by-test-run/{test_run_id}` | List assurance runs for an evaluation run |
| GET | `/assurance-tools` | Check optional Garak/DeepEval dependency availability |
| POST | `/assurance-tools/garak/{test_run_id}` | Run an allowlisted authorized Garak configuration |
| GET | `/assurance-tools/runs/{test_run_id}` | Inspect persisted tool execution results |
| POST | `/assurance-tools/deepeval/{test_run_id}` | Run supported DeepEval metrics |
| GET | `/ui` | Serve the local frontend |

`POST /certificates` accepts `{"test_run_id": 1}` only. The score is calculated
from that run's persisted completed results. Caller-supplied scores are rejected.
The response identifies the source run and labels the record
`INTERNAL_UNSIGNED_ASSESSMENT`; it is not formal certification.

When `API_TOKEN` is configured, sensitive APIs require a Bearer token. When unset, protected APIs are limited to loopback clients; health, UI, and docs remain accessible. This is a local-use guard, not production identity/authorization. Provider availability indicates configuration only, not a successful live connection. The benchmark is synthetic, and external packages are optional and unverified in this environment.
