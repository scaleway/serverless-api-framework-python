from typing import Any, List, Union
from typing_extensions import Unpack

from scw_serverless.config.function import Function, FunctionKwargs
from scw_serverless.events.schedule import CronSchedule


class Serverless:
    def __init__(self, service_name: str, env: dict = None, secret: dict = None):
        self.functions: List[Function] = []
        self.service_name: str = service_name
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
        inputs: dict[str, Any] = {},
        **kwargs: Unpack[FunctionKwargs],
    ):
        """Schedules a handler with Cron, passing input as parameters to the body.

        :param schedule: Cron schedule to run with
        :type schedule: Cron
        :param inputs: Parameters to be passed to the body, defaults to {}
        :type inputs: Optional[dict[str, Any]], optional
        """
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
