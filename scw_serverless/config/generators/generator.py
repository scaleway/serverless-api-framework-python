from abc import ABC, abstractmethod


def Generator(ABC):
    @abstractmethod
    def write(self, path: str) -> None:
        pass
