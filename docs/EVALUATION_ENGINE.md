# Evaluation engine

The current evaluator compares an expected string and a provider response using:

- **Exact match**: 1 when normalized strings match exactly, otherwise 0.
- **Similarity**: `difflib.SequenceMatcher` character-sequence similarity in the range [0, 1]. It is not embedding-based semantic similarity.
- **Combined score**: `0.3 * exact_match + 0.7 * similarity`, rounded to four decimal places.
- **Hallucination-related heuristic**: lexical overlap between distinct words in expected and actual responses. A low overlap is flagged; this is not source-grounded factuality or validated hallucination detection.

Metrics are implemented in `backend/app/engines/evaluation_engine/`. Risk policy thresholds and attack/hallucination modifiers are project heuristics. Scores and generated certificate evidence are not regulatory certification, independent accreditation, or a guarantee of safety.

Cases may be associated with a test run or a dataset. New dataset-bound runs freeze case IDs and case content, and record the dataset version and hash. Historical dataset runs retain ID-based case lookup because their original content was not stored. For backward compatibility, a non-dataset run with no run-scoped cases falls back to all unscoped legacy cases. Evaluation runs are single-use; create a new run to repeat an evaluation.

EGAA separately estimates evidence gaps across eight risk dimensions and chooses bounded tests by risk-weighted expected gap reduction per estimated cost. It discounts stale, mocked, and simulated evidence and raises uncertainty on contradictions. The method is a prioritization aid; the bundled benchmark is synthetic and the existing evaluation metrics remain heuristic. See the [adaptive assurance POV](POV_ADAPTIVE_ASSURANCE.md).

## Offline hallucination evaluation

`POST /evaluation/hallucination` accepts a non-empty `prompt`, `response`, and optional `reference_context` (a string or list of documents). It extracts response sentences and assigns each to one primary category. The check is deterministic and offline; it does not call an LLM, DeepEval, or a paid provider. Exact text matches count as supported. Only explicit numeric/negation conflicts are treated as contradicted. Claims without direct text support are unsupported when references are present, and unverifiable when they are absent. Citation markers are checked only when the supplied references contain structured citation markers or URLs.

Scores use `100 * (supported + 0.5 * unsupported) / (supported + contradicted + unsupported)`. Unverifiable claims are excluded, and the score is unavailable if no claims can be checked. Each sentence contributes once to the score. Unsupported means no direct textual match, not proven false; the method is a lexical heuristic rather than semantic fact verification.

The category registry reports factual errors, entity errors, temporal inaccuracies, unsupported claims, context contradictions, and citation hallucinations as partial or bounded checks. Relationship errors, fabricated information as a general category, logical inconsistencies, and instruction/constraint inconsistencies are explicitly marked unimplemented. This endpoint returns a category scorecard and risk summary without modifying persisted legacy evaluation runs, scorecards, certificates, or reports.
