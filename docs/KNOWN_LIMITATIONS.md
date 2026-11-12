# Known limitations

- The default provider is a deterministic mock that always returns `Mock response.`; it does not evaluate a real model.
- The default metric called `similarity` is character-sequence similarity, not semantic or embedding similarity.
- Hallucination detection is lexical word overlap against an expected answer, not source-grounded factuality checking.
- New dataset-bound runs snapshot case IDs, dataset version, a content hash, and the selected case content. Historical dataset runs created before the content-snapshot migration cannot be backfilled and continue to load their cases by ID. Existing unscoped cases remain a legacy fallback for non-dataset runs that have no run-scoped cases.
- Evaluation runs are single-use; a repeated attempt is rejected instead of appending duplicate results. Create a new run to retry. There is no resume/recovery flow for a process interrupted while a run is `RUNNING`.
- Provider status reports configuration only, not live service health. The shared LiteLLM client enforces a 30-second timeout and retries once for connection/service-unavailable errors; real-provider success, billing, and failover are not validated.
- The built-in attack set is only three static probes with keyword response detection.
- Garak and DeepEval adapters exist, but the optional packages are not installed and actual invocations are unverified. PyRIT and Promptfoo remain unintegrated.
- Risk scores and certificates are project-defined heuristics/evidence records, not independent certification or safety guarantees.
- A provider failure is recorded as a failed evaluation case with a generic, non-sensitive error message. Any failed case (including mixed success/failure) or zero-case run is `FAILED`; failed/incomplete runs cannot receive an assessment. Assessment score and evidence are derived only from persisted completed results for the requested run, and the record is explicitly internal and unsigned.
- API_TOKEN-based Bearer protection and loopback-only fallback restrict sensitive API routes, but this is not production authentication, user authorization, rate limiting, or a full CSRF/network threat model. Do not expose this prototype to an untrusted network.
- Alembic provides an additive migration for the assurance and dataset schema; it is not yet a complete historical migration chain for every legacy table.
- The adaptive benchmark uses synthetic fixtures, not real-model evidence. The static attack probes are limited to three patterns. Similarity and factuality measures remain heuristics.
- EGAA's time budget cannot interrupt a blocking Python callback. Garak's subprocess runner enforces its own timeout.
- Live model calls, Redis, Docker, deployment, committed browser tests, and production security have not been validated.
