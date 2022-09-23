from abc import ABC, abstractmethod


class Generator(ABC):
    @abstractmethod
    def write(self, path: str) -> None:
        pass
