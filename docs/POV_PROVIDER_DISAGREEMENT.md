# POV 2 — Treat provider disagreement as an uncertainty signal, not a vote

**Status:** Internal point of view, prepared for review in this repository; not externally published or independently peer-reviewed.  
**Audience:** AI product, model-evaluation, assurance, and governance teams.  
**Question:** What should a multi-provider system conclude when models give different answers?

## Executive position

Disagreement among model outputs is evidence of uncertainty about response stability, not proof that one provider is correct or that a majority is safe. A provider ensemble can reveal that an answer depends on model choice, but agreement can still be jointly wrong, biased, or based on shared blind spots.

Use disagreement to prioritize verification, not to auto-select a winner. Preserve each model's identity, version, prompt, configuration, and output; distinguish semantic disagreement from harmless wording variation; and resolve high-impact conflicts with evidence external to the providers or an accountable human reviewer.

## Rationale

A production system can vary by provider, model version, decoding settings, prompt template, tools, and retrieved context. A text difference can be stylistic, while two identical answers can share the same unsupported assumption. Therefore, a single "consensus" score discards important context. Risk management should make uncertainty and limitations visible rather than converting model agreement into a trust claim [1, 2].

## Proposed operating model

1. **Define comparability first.** Replay the same task, system instruction, context, tool permissions, and output schema. Record configuration drift.
2. **Separate disagreement classes.** Track lexical difference, semantic contradiction, evidence/provenance difference, policy divergence, and refusal variation as distinct signals.
3. **Avoid majority-vote truth.** Treat provider count as a measure of breadth, not correctness. Agreement is not independent if models share training data, architecture, prompts, or source material.
4. **Escalate by impact.** High-impact disagreement should trigger source-backed verification, a controlled task-specific test, or a human review—not automatic provider switching.
5. **Record negative and missing evidence.** Timeout, refusal, malformed output, and unavailable providers should be represented as missing/failed evidence, not silently omitted.
6. **Bound comparison costs and privacy exposure.** Replays may send sensitive prompts to multiple external services. Require authorization, data minimization, and explicit billing approval.
7. **Calibrate before thresholds.** Establish labeled data, false-alarm/false-agreement rates, and subgroup analysis before a disagreement score influences release decisions.

## What AAOS implements—and does not

AAOS defines a `provider_disagreement` risk and a bounded replay catalog entry. Its current comparison looks at stored outputs for the same evaluation case and uses character similarity as an uncertainty signal. It does not automatically call another provider, determine semantic contradiction, establish the factual answer, or recommend a provider winner. The adaptive route is mock-only, and its provider replay behavior has no live multi-model demonstration.

Character similarity can overstate disagreement between paraphrases and miss logical contradictions with overlapping words. The signal should therefore be described as a crude text-variation indicator, not a semantic disagreement metric. The synthetic benchmark's contradictory-provider scenario only tests deterministic bookkeeping.

## Recommendations

- Rename and document the current measure as output variation until semantic validation exists.
- Require exact configuration matching or explicitly report mismatches before comparing outputs.
- Add task-specific semantic/claim-level comparison with independent, source-backed adjudication and calibrated thresholds.
- Track model/version and source independence; do not assume providers are statistically independent.
- Keep raw outputs access-controlled and define retention/redaction rules.
- Use disagreements to trigger targeted tests or human verification, and keep the final decision accountable to a named owner.

## Conclusion

Cross-provider comparison is valuable as an uncertainty and monitoring mechanism, but unsafe as a truth oracle. AAOS captures the beginnings of this idea while deliberately labeling its present signal as limited. An operational system needs task-level validation, provenance, privacy controls, and independent adjudication before using disagreement in governance decisions.

## References

1. NIST, [Artificial Intelligence Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/itl/ai-risk-management-framework), NIST AI 100-1, 2023.
2. C. Autio et al., [Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile](https://doi.org/10.6028/NIST.AI.600-1), NIST AI 600-1, 2024.
3. AAOS implementation: [provider comparison and evidence handling](../backend/app/services/assurance_service.py) and [EGAA risk taxonomy](../backend/app/engines/assurance/egaa.py).
