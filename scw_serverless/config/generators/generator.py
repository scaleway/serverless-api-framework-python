import logging
from abc import ABC, abstractmethod
from typing import Any

from scw_serverless.config.function import Function


class Generator(ABC):
    @abstractmethod
    def write(self, path: str) -> None:
        pass

    @staticmethod
    @abstractmethod
    def get_allowed_args() -> dict[str, str]:
        pass

    def get_fn_args(self, fn: Function) -> dict[str, Any]:
        allowed_args = self.get_allowed_args()
        config = {}
        for k, v in fn.args.items():
            if k in allowed_args:
                if isinstance(v, int):
                    config[allowed_args[k]] = str(v)
                else:
                    config[allowed_args[k]] = v
            else:
                # TODO: change this for custom logger
                logging.warning(
                    "found unsupported argument %s for %s"
                    % (k, self.__class__.__name__)
                )
        return config
