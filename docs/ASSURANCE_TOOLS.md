# Assurance tool exploration

AAOS implements adapters in two different assurance-tool categories. The dependencies are intentionally optional and are not installed by the default environment. `/assurance-tools` reports whether a dependency is importable; mocked tests validate adapter control paths, not the underlying external tools.

Execution records (including dependency blockers, failures, metrics, findings,
and artifact paths) are saved against a test run and can be retrieved with
`GET /assurance-tools/runs/{test_run_id}`. The UI displays this persisted
history when a run is selected. It never substitutes a mock result for a
missing external tool.

## Category 1: LLM vulnerability scanner — Garak

Garak is an LLM vulnerability scanner. AAOS's optional runner:

- invokes `python -m garak` with a subprocess argument list (`shell=False`);
- accepts only allowlisted probe names and model types;
- requires explicit authorization and confirmation before invocation;
- applies a configurable subprocess timeout, captures and redacts output, stores artifacts, normalizes failure findings, and records the run;
- does not permit arbitrary target URLs or shell commands through the API.

The UI selects a `test.Blank` test generator; this proves UI/API plumbing only and is not an assessment of an actual model. Garak is not installed here and no actual scan has run. The parser and timeout/authorization behavior are covered with mocked subprocess tests. Before using Garak on a model, install it in a reviewed environment and obtain explicit owner authorization.

The runner uses Garak's documented `python -m garak` interface and
`--report_prefix`; its failure-line parser matches the documented console form
`probe detector: FAIL ...`. This was checked against Garak documentation, not
against an installed package or a completed scan in this environment.

The UI's safe test-generator request uses `model_type: "test"`,
`model_name: "test.Blank"`, an allowlisted probe, and
`authorization_confirmed: true`. For an explicitly authorized real target, the
API additionally requires `external_target_confirmed: true`; do not use that
option without target-owner approval. Execution results are retrievable from
`GET /assurance-tools/runs/{test_run_id}`.

## Category 2: deterministic and judge-based evaluation metrics — DeepEval

AAOS supports:

- `exact_match`: deterministic string equality, requiring no LLM judge;
- `answer_relevancy`: judge-based, requiring a configured judge model and explicit confirmation of external calls.

Per-case/per-metric status and partial failures are retained. The API does not silently convert failures into passing results. The UI offers exact match only. DeepEval is not installed here; the adapter is tested using fake metric classes. No metric was run against the actual DeepEval package.

The UI posts its selected run's completed prompt, actual output, and expected
output to `/assurance-tools/deepeval/{test_run_id}` with
`metrics: ["exact_match"]`. `answer_relevancy` is judge-backed and remains
disabled unless both server configuration and per-request confirmation allow
external judge calls.

DeepEval documents Exact Match as a non-LLM exact string comparison and Answer Relevancy as an LLM-as-a-judge metric; see the [official Exact Match documentation](https://deepeval.com/docs/metrics-exact-match) and [Answer Relevancy documentation](https://deepeval.com/docs/metrics-answer-relevancy). Garak's overview is in its [official documentation](https://docs.garak.ai/garak/welcome-to-garak.md).

## Local built-in probes

The in-app security workflow comprises three static probes and keyword-oriented response analysis. It is not equivalent to Garak's broader scanner or to a security evaluation of an actual model.

## Execution and safety

Optional packages are not in the default `backend/requirements.txt`. Tool results are persisted, with environment status and blockers visible from the UI/API. The adaptive endpoint is restricted to mock provider mode; a live judge call requires explicit settings and request confirmation. Do not point probes at a third-party system without written authorization. Test commands shown in the suite replace subprocesses/metrics with fakes and do not execute external targets.
