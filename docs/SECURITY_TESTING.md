# Security testing

The built-in security workflow consists of three static probe prompts and keyword-oriented response analysis. It is a small controlled smoke test, not a comprehensive red-team evaluation. Tests are executed only against the currently configured provider; configure the deterministic mock for local checks to avoid external calls.

The local test suite verifies the probe endpoint against the mock and tests the Garak subprocess authorization, timeout, and output-normalization boundaries with a fake subprocess. It tests DeepEval adapter partial failures with fake metric classes. These are control-flow tests, not scans of a real model. Garak and DeepEval are optional but not installed in the verified environment; PyRIT and Promptfoo are not integrated.

When `API_TOKEN` is configured, sensitive APIs require a Bearer token; without one, those routes are loopback-only. Health/UI/docs remain public. This local guard is not a full identity or role-based authorization system and does not make the application safe for public exposure. Do not point probes at external systems without authorization and explicit confirmation of data handling and possible provider cost. AAOS risk scores and certificates are heuristic assessment artifacts, not security certification.
