# Engineering innovation note — Evidence-gap-guided AI assurance

**Status:** Candidate engineering contribution for internal IP review; no patentability, novelty, or ownership determination has been made.  
**Inventorship/legal review:** Required before any external IP claim or filing.

## Candidate contribution

AAOS implements a prototype method for choosing the next AI assurance test from an evidence ledger. Rather than relying only on static checklists, it combines risk-weighted evidence gaps with evidence confidence, age, provenance mode, contradictions, test dependencies, execution limits, and estimated costs. The system emits an explainable ranking, preserves failed/skipped/unknown evidence, updates the ledger after execution, and returns a bounded stop status.

## Technical elements present in the implementation

- A typed risk taxonomy and test catalog with scope, cost, expected strength/confidence, dependencies, and run limits.
- Evidence valuation using strength × confidence × exponential freshness decay × real/mocked/simulated mode.
- Per-risk uncertainty and contradiction adjustments, with explicit handling so failed, timed-out, skipped, and unknown results earn no evidence credit.
- Deterministic next-test selection by risk-weighted expected gap reduction per estimated cost, with reasons for all considered candidates.
- A bounded adaptive loop that persists the evidence and decision history and distinguishes incomplete evidence from critical-risk failure.
- A synthetic, reproducible fixed-versus-adaptive benchmark and a mock-only API execution boundary.

## Prototype evidence

The automated suite tests the gap formula, freshness and mode discounting, contradiction, missing/failed evidence, selector determinism, dependencies, budgets, and persistence. The reproducible benchmark compares the same six-test fixed suite with the
bounded adaptive selector over three authored scenarios. Adaptive execution
uses two tests with equal fixture coverage in the strong-evidence scenario
(0.7605), stops after one critical security finding in the seeded-gap scenario
(coverage 0.3752 versus fixed 0.4004; both detect the seeded failure), and uses
two tests with equal coverage in the contradictory-evidence scenario (1.0000).
These values are synthetic fixture outputs, not real-world efficacy evidence
or a demonstrated performance advantage.

## Why this is only an IP candidate

The present code is a prototype composition of concepts that may have known prior art: weighted risk assessment, test prioritization, freshness decay, evidence provenance, and cost-sensitive selection. No systematic prior-art search, claim drafting, inventorship review, or legal analysis has been conducted. A technical implementation alone does not establish that the approach qualifies for patent or other IP protection.

Before any protection claim:

1. preserve dated design and implementation records and identify human contributors;
2. have counsel conduct a prior-art search across assurance selection, active testing, evidence aggregation, and risk-based testing;
3. distinguish what is technically new from standard scoring/selection practices;
4. evaluate novelty, non-obviousness, ownership, disclosure timing, and filing strategy with counsel;
5. validate the method on representative, authorized systems against fixed and alternative adaptive baselines.

## References and implementation

- [EGAA engine](../backend/app/engines/assurance/egaa.py)
- [Synthetic benchmark](../backend/app/engines/assurance/benchmark.py)
- [Adaptive assurance API/service](../backend/app/services/assurance_service.py)
- [POV: From fixed suites to adaptive assurance](POV_ADAPTIVE_ASSURANCE.md)
- [Known limitations](KNOWN_LIMITATIONS.md)
