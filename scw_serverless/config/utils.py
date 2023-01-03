from abc import ABC
from dataclasses import asdict
from typing import Any


class _SerializableDataClass(ABC):
    def asdict(self) -> dict[str, Any]:
        """Converts to a dictionnary, ignoring None values"""
        return asdict(
            self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
        )
