from abc import ABC, abstractmethod


class Event(ABC):
    def __init__(self) -> None:
        super().__init__()

    @property
    @abstractmethod
    def kind(self) -> str:
        return ""
