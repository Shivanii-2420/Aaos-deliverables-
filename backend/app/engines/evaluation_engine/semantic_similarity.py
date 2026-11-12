from collections import Counter
import math
import re


def semantic_similarity_score(
    expected: str,
    actual: str
) -> float:

    """Compute cosine similarity between term-frequency vectors of two texts.

    This is a simple, dependency-free alternative to embedding-based
    similarity. It performs much better than raw token-overlap for
    paraphrased answers.
    """

    if not expected or not actual:
        return 0.0

    expected_tokens = re.findall(r"\w+", expected.lower())
    actual_tokens = re.findall(r"\w+", actual.lower())

    if not expected_tokens or not actual_tokens:
        return 0.0

    exp_counter = Counter(expected_tokens)
    act_counter = Counter(actual_tokens)

    # Dot product
    intersection = set(exp_counter.keys()) & set(act_counter.keys())
    dot = sum(exp_counter[w] * act_counter[w] for w in intersection)

    # Norms
    norm_exp = math.sqrt(sum(v * v for v in exp_counter.values()))
    norm_act = math.sqrt(sum(v * v for v in act_counter.values()))

    if norm_exp == 0 or norm_act == 0:
        return 0.0

    score = dot / (norm_exp * norm_act)

    return round(score, 4)