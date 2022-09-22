from typing import Any, List, Optional

from .utils import to_camel_case, module_to_path
from .events.cron import Cron


class _Function:
    def __init__(self, handler, args: dict[str, Any]) -> None:
        self.name: str = handler.__name__
        self.handler_path: str = (
            module_to_path(handler.__module__) + "." + handler.__name__
        )

        self.args: dict[str, Any] = args

    def _get_args_dict(self) -> dict[str, Any]:
        allowed_args = (
            [  # List of allowed args in serverless framework function configuration
                "env",
                "secret",
                "min_scale",
                "max_scale",
                "max_concurrency",
                "memory_limit",
                "timeout",
                "custom_domains",
                "privacy",
                "description",
            ]
        )
        config = {}
        for k, v in self.args.items():
            if k in allowed_args:
                if k == "custom_domains":
                    config[k] = v
                else:
                    config[to_camel_case(k)] = v
        return config

    def get_config(self) -> dict[str, Any]:
        return {"handler": self.handler_path} | self._get_args_dict()


class _ScheduledFunction(_Function):
    def __init__(
        self,
        schedule: Cron,
        inputs: Optional[dict[str, Any]],
        handler,
        args: dict[str, Any],
    ) -> None:
        super().__init__(handler, args)
        self.inputs = inputs
        self.schedule = schedule

    def _get_schedule_config(self) -> dict[str, Any]:
        schedule_config = {"rate": self.schedule.as_expression()}
        if self.inputs is not None:
            schedule_config["input"] = self.inputs
        return {"schedule": schedule_config}

    def get_config(self) -> dict[str, Any]:
        config = super().get_config()
        config["events"] = [self._get_schedule_config()]
        return config


class Serverless:
    def __init__(self, service_name: str, env: dict = None, secret: dict = None):
        self.functions: List[_Function] = []
        self.service_name: str = service_name
        self.env = env
        self.secret = secret

    def func(self, **kwargs):
        """
        @func decorator

        :param kwargs:
        :return:
        """

        def decorator(handler):
            self.functions.append(_Function(handler, kwargs))

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return decorator

    def schedule(
        self, schedule: Cron, inputs: Optional[dict[str, Any]] = None, **kwargs
    ):
        """Schedules a handler with Cron, passing input as parameters to the body.

        :param schedule: Cron schedule to run with
        :type schedule: Cron
        :param inputs: Parameters to be passed to the body, defaults to None
        :type inputs: Optional[dict[str, Any]], optional
        """

        def decorator(handler):
            self.functions.append(_ScheduledFunction(schedule, inputs, handler, kwargs))

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return decorator
