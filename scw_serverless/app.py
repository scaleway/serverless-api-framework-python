from typing import Any, List, Union, Optional
from typing_extensions import Unpack

from scw_serverless.config.function import Function, FunctionKwargs
from scw_serverless.events.schedule import CronSchedule


class Serverless:
    def __init__(
        self,
        service_name: str,
        gateway_domains: Optional[list[str]] = None,
        env: Optional[dict[str, Any]] = None,
        secret: Optional[dict[str, Any]] = None,
    ):
        self.functions: List[Function] = []
        self.service_name: str = service_name
        self.gateway_domains: list[str] = gateway_domains if gateway_domains else []
        self.env = env
        self.secret = secret

    def func(
        self,
        **kwargs: Unpack[FunctionKwargs],
    ):
        """
        @func decorator

        :param kwargs:
        :return:
        """

        def decorator(handler):
            self.functions.append(
                Function.from_handler(
                    handler,
                    kwargs,
                )
            )

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return decorator

    def schedule(
        self,
        schedule: Union[str, CronSchedule],
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: Unpack[FunctionKwargs],
    ):
        """Schedules a handler with Cron, passing input as parameters to the body.

        :param schedule: Cron schedule to run with
        :type schedule: Cron
        :param inputs: Parameters to be passed to the body, defaults to {}
        :type inputs: Optional[dict[str, Any]], optional
        """
        inputs = inputs if inputs else {}

        if isinstance(schedule, str):
            schedule = CronSchedule.from_expression(schedule, inputs)
        else:
            schedule.inputs |= inputs

        def decorator(handler):
            self.functions.append(
                Function.from_handler(handler, kwargs, events=[schedule])
            )

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return decorator

    def get(self, path: str, **kwargs: Unpack[FunctionKwargs]):
        kwargs |= {"path": path, "methods": ["GET"]}
        return self.func(**kwargs)

    def post(self, path: str, **kwargs: Unpack[FunctionKwargs]):
        kwargs |= {"path": path, "methods": ["POST"]}
        return self.func(**kwargs)

    def put(self, path: str, **kwargs: Unpack[FunctionKwargs]):
        kwargs |= {"path": path, "methods": ["PUT"]}
        return self.func(**kwargs)

    def delete(self, path: str, **kwargs: Unpack[FunctionKwargs]):
        kwargs |= {"path": path, "methods": ["DELETE"]}
        return self.func(**kwargs)

    def patch(self, path: str, **kwargs: Unpack[FunctionKwargs]):
        kwargs |= {"path": path, "methods": ["PATCH"]}
        return self.func(**kwargs)
