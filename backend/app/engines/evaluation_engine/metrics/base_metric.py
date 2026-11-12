from abc import ABC
from abc import abstractmethod


class BaseMetric(ABC):

    name = "base"

    @abstractmethod
    def evaluate(
        self,
        expected: str,
        actual: str
    ) -> float:
        raise NotImplementedError(
            "Subclasses must implement evaluate()"
        )
