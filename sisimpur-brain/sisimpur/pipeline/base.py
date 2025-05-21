from abc import ABC, abstractmethod


class Step(ABC):
    @abstractmethod
    def run(self, context: dict) -> dict:
        pass
