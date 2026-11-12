import re
from dataclasses import dataclass
from typing import Any

from backend.app.engines.risk_engine.calculator import RiskCalculator


@dataclass(frozen=True)
class CategoryDefinition:
    name: str
    status: str
    description: str


_CATEGORIES = (
    CategoryDefinition(
        "factual_errors",
        "partial",
        "Detects explicit numeric or negation conflicts with supplied context.",
    ),
    CategoryDefinition(
        "entity_errors",
        "partial",
        "Surfaces named-entity claims that lack direct textual support.",
    ),
    CategoryDefinition(
        "relationship_errors",
        "not_implemented",
        "Entity relationship entailment is not reliably evaluated.",
    ),
    CategoryDefinition(
        "fabricated_information",
        "not_implemented",
        "Fabrication cannot be established without a reliable external source.",
    ),
    CategoryDefinition(
        "unsupported_claims",
        "working",
        "Checks for direct textual support in supplied reference context.",
    ),
    CategoryDefinition(
        "context_contradictions",
        "partial",
        "Detects explicit numeric or negation conflicts with supplied context.",
    ),
    CategoryDefinition(
        "citation_hallucinations",
        "partial",
        "Checks citation markers only when references expose matching markers.",
    ),
    CategoryDefinition(
        "logical_inconsistencies",
        "not_implemented",
        "General logical consistency is not evaluated.",
    ),
    CategoryDefinition(
        "temporal_inaccuracies",
        "partial",
        "Detects explicit date or year conflicts with supplied context.",
    ),
    CategoryDefinition(
        "instruction_inconsistencies",
        "not_implemented",
        "Instruction and constraint compliance is not evaluated.",
    ),
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"[a-z0-9]+")
_NUMBER = re.compile(r"\b\d+(?:[.,]\d+)*\b")
_CITATION = re.compile(r"\[\s*\d+\s*\]")
_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_YEAR_OR_DATE = re.compile(
    r"\b(?:1[0-9]{3}|20[0-9]{2}|21[0-9]{2})\b"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
)
_NEGATION = {"no", "not", "never", "neither", "without"}
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "for",
    "from", "had", "has", "have", "in", "into", "is", "it", "its",
    "of", "on", "or", "that", "the", "their", "this", "to", "was",
    "were", "will", "with",
}
_SENTENCE_STARTERS = {
    "a", "an", "according", "at", "first", "in", "it", "on", "the",
    "there", "this", "that",
}
_NAMED_ENTITY = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCE_SPLIT.split(text) if part.strip()]


def _normalized(text: str) -> str:
    return " ".join(_WORD.findall(text.lower()))


def _terms(text: str) -> set[str]:
    return {
        word for word in _WORD.findall(text.lower())
        if word not in _STOP_WORDS
    }


def _entities(text: str) -> set[str]:
    entities = set()
    for match in _NAMED_ENTITY.finditer(text):
        words = match.group().split()
        if words[0].lower() in _SENTENCE_STARTERS:
            words = words[1:]
        if len(words) >= 2:
            entities.add(_normalized(" ".join(words)))
    return entities


def _category_for_claim(claim: str) -> str:
    if _CITATION.search(claim) or _URL.search(claim):
        return "citation_hallucinations"
    if _YEAR_OR_DATE.search(claim):
        return "temporal_inaccuracies"
    if _entities(claim):
        return "entity_errors"
    if _NUMBER.search(claim):
        return "factual_errors"
    return "unsupported_claims"


def _find_reference(claim: str, references: list[str]) -> tuple[str, str | None]:
    normalized_claim = _normalized(claim)
    if not normalized_claim:
        return "unverifiable", None

    for reference in references:
        if normalized_claim in _normalized(reference):
            return "supported", reference

    claim_terms = _terms(claim)
    claim_numbers = set(_NUMBER.findall(claim))
    claim_negated = bool(_terms(claim) & _NEGATION)
    for reference in references:
        for sentence in _sentences(reference):
            reference_terms = _terms(sentence)
            shared_terms = claim_terms & reference_terms
            reference_numbers = set(_NUMBER.findall(sentence))
            numbers_conflict = (
                bool(claim_numbers)
                and bool(reference_numbers)
                and claim_numbers != reference_numbers
            )
            negation_conflict = (
                claim_negated != bool(reference_terms & _NEGATION)
                and len(shared_terms) >= 2
            )
            overlap = len(shared_terms) / max(
                len(claim_terms | reference_terms), 1
            )
            if (
                len(shared_terms) >= 2
                and overlap >= 0.30
                and (numbers_conflict or negation_conflict)
            ):
                return "contradicted", sentence

    return "unsupported", None


def _citation_state(claim: str, references: list[str]) -> tuple[str, str]:
    response_markers = set(_CITATION.findall(claim))
    response_urls = set(_URL.findall(claim))
    reference_text = "\n".join(references)
    if not references:
        return (
            "unverifiable",
            "Citation cannot be checked without supplied reference context.",
        )

    reference_markers = set(_CITATION.findall(reference_text))
    reference_urls = set(_URL.findall(reference_text))
    has_structured_references = bool(reference_markers or reference_urls)
    if not has_structured_references:
        return (
            "unverifiable",
            "References contain no citation identifiers to compare.",
        )
    if response_markers <= reference_markers and response_urls <= reference_urls:
        return (
            "supported",
            "Citation marker matches an identifier present in the references.",
        )
    return (
        "unsupported",
        "Citation marker does not match an identifier present in the references.",
    )


class HallucinationEvaluationEngine:
    """Conservative, offline reference-grounding checks; not an LLM judge."""

    @staticmethod
    def categories() -> list[dict[str, str]]:
        return [
            {
                "name": item.name,
                "status": item.status,
                "description": item.description,
            }
            for item in _CATEGORIES
        ]

    @staticmethod
    def evaluate(
        prompt: str,
        response: str,
        reference_context: str | list[str] | None = None,
    ) -> dict[str, Any]:
        del prompt  # Retained in the interface for future prompt-constraint checks.
        references = (
            [reference_context]
            if isinstance(reference_context, str) and reference_context.strip()
            else [
                item.strip()
                for item in (reference_context or [])
                if isinstance(item, str) and item.strip()
            ]
        )
        reference_sentences = [
            sentence
            for reference in references
            for sentence in _sentences(reference)
        ]
        claims = _sentences(response)
        findings = []

        for claim in claims:
            category = _category_for_claim(claim)
            evidence: str | None
            if category == "citation_hallucinations":
                status, explanation = _citation_state(claim, references)
                evidence = explanation
            elif not reference_sentences:
                status = "unverifiable"
                evidence = "No reference context was supplied."
                explanation = (
                    "No reference was supplied; the claim is not treated as false."
                )
            else:
                status, matched_reference = _find_reference(
                    claim, reference_sentences
                )
                evidence = (
                    matched_reference
                    if matched_reference
                    else "No direct textual match or explicit conflict found."
                )
                if status == "supported":
                    explanation = "Claim text is directly present in supplied context."
                elif status == "contradicted":
                    explanation = "Claim conflicts with the cited reference sentence."
                else:
                    explanation = "No direct textual support was found in the references."
            findings.append({
                "claim": claim,
                "category": category,
                "status": status,
                "severity": (
                    "HIGH" if status == "contradicted"
                    else "MEDIUM" if status == "unsupported"
                    else "LOW"
                ),
                "evidence": evidence,
                "explanation": explanation,
            })

        state_counts = {
            state: sum(1 for finding in findings if finding["status"] == state)
            for state in ("supported", "contradicted", "unsupported", "unverifiable")
        }
        category_scores = {}
        for category in _CATEGORIES:
            category_findings = [
                item for item in findings if item["category"] == category.name
            ]
            scoreable = [
                item for item in category_findings
                if item["status"] != "unverifiable"
            ]
            category_scores[category.name] = {
                "score": _score(scoreable),
                "status": category.status,
                "claims_evaluated": len(category_findings),
                "description": category.description,
            }

        overall_score = _score([
            item for item in findings if item["status"] != "unverifiable"
        ])
        risk = None
        if overall_score is not None:
            risk = RiskCalculator.calculate(
                overall_score / 100,
                hallucinations=state_counts["contradicted"],
            )

        return {
            "claim_count": len(claims),
            **state_counts,
            "overall_hallucination_score": overall_score,
            "category_scores": category_scores,
            "claims": findings,
            "problematic_claims": [
                item for item in findings
                if item["status"] in {"contradicted", "unsupported"}
            ],
            "risk": risk,
            "scoring": {
                "formula": (
                    "100 * (supported + 0.5 * unsupported) / "
                    "(supported + contradicted + unsupported); "
                    "unverifiable claims are excluded."
                ),
                "supported_weight": 1.0,
                "contradicted_weight": 0.0,
                "unsupported_weight": 0.5,
                "unverifiable_weight": None,
                "double_counting": (
                    "Each extracted sentence is assigned to one primary "
                    "category and contributes once to the overall score."
                ),
            },
            "limitations": [
                "Text matching and explicit numeric/negation rules are conservative heuristics, not semantic fact verification.",
                "Reference-free factual claims and unavailable categories remain unverifiable or unimplemented.",
                "An LLM judge or paid provider is not used.",
            ],
        }


def _score(findings: list[dict[str, Any]]) -> float | None:
    if not findings:
        return None
    weighted = sum(
        1.0 if item["status"] == "supported"
        else 0.5 if item["status"] == "unsupported"
        else 0.0
        for item in findings
    )
    return round(100 * weighted / len(findings), 2)
