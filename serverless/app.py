from typing import Any, List, Optional

import serverless.utils as utils
from serverless.events.cron import Cron


class _Function:
    def __init__(self, handler, args: dict[str, Any]) -> None:
        self.name: str = handler.__name__
        self.handler_path: str = (
            utils.module_to_path(handler.__module__) + "." + handler.__name__
        )

        self.args: dict[str, Any] = args

    def _add_args(self, config):
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
        for k, v in self.args.items():
            if k in allowed_args:
                if k == "custom_domains":
                    config[k] = v
                else:
                    config[utils.to_camel_case(k)] = v

    def add_func_to_config(self, config: dict[str, Any]) -> None:
        config["functions"] |= {self.name: {"handler": self.handler_path}}
        self._add_args(config["functions"][self.name])


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

    def _add_schedule(self, config: dict[str, Any]) -> None:
        if "events" not in config["functions"][self.name]:
            config["functions"][self.name]["events"] = []
        schedule_config = {"rate": self.schedule.as_expression()}
        if self.inputs is not None:
            schedule_config["input"] = self.inputs
        config["functions"][self.name]["events"].append({"schedule": schedule_config})

    def add_func_to_config(self, config: dict[str, Any]) -> None:
        super().add_func_to_config(config)
        self._add_schedule(config)


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

    def schedule(self, schedule: Cron, inputs: Optional[dict[str, Any]] = None, **kwargs):
        def decorator(handler):
            self.functions.append(_ScheduledFunction(schedule, inputs, handler, kwargs))

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return decorator
