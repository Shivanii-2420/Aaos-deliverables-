def exact_match_score(
    expected: str,
    actual: str
) -> float:

    if (
        expected is None
        or actual is None
        or expected.strip() == ""
        or actual.strip() == ""
    ):
        return 0.0

    if (
        expected.strip().lower()
        ==
        actual.strip().lower()
    ):
        return 1.0

    return 0.0
