from abc import ABC, abstractmethod


class Generator(ABC):
    """Generates some deployment configuration."""

    @abstractmethod
    def write(self, path: str) -> None:
        """Writes the configuration to path"""
