from abc import ABC, abstractmethod
from typing import Any

from ...config.function import Function


class Generator(ABC):
    @abstractmethod
    def write(self, path: str) -> None:
        pass

    # @abstractmethod
    # def validate_function_args(self, fn: Function) -> None:
    #     pass

    # @abstractmethod
    # def config_from_function(self, fn: Function) -> dict[str, Any]:
    #     pass
