class MockAdapter:
    """Deterministic local provider used for safe development and testing."""

    @staticmethod
    def generate(prompt: str) -> str:
        del prompt
        return "Mock response."
