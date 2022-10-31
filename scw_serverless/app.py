from typing import Any, Callable, List, Optional, Union

from typing_extensions import Unpack

from scw_serverless.config.function import Function, FunctionKwargs
from scw_serverless.events.schedule import CronSchedule
from scw_serverless.utils.http import HTTPMethod


class Serverless:
    """Manage your Serverless Functions.

    :param service_name: name of the namespace
    :param gateway_domains: domains to be supported by the gateway (default [])
    :param env: namespace level environment variables (default {})
    :param secret: namespace level secrets (default {})
    """

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
    ) -> Callable:
        """Define a Serverless handler and its parameters from the keyword arguments.

        See ``FunctionKwargs`` for all possible parameters.

        *Note:* Some parameters may not be supported by a specific backend.

        *Example:*

        .. highlight:: python
        .. code-block:: python
            app = Serverless("example")
            app.func(privacy="public", env={"key": "value"})
            def handler(event, context)
                ...
        """

        def _decorator(handler: Callable):
            self.functions.append(
                Function.from_handler(
                    handler,
                    kwargs,
                )
            )

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return _decorator

    def schedule(
        self,
        schedule: Union[str, CronSchedule],
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: Unpack[FunctionKwargs],
    ) -> Callable:
        """Define a scheduled handler with Cron, passing input as parameters.

        :param schedule: Cron schedule to run with
        :param inputs: parameters to be passed to the body (default to {})
        """
        inputs = inputs if inputs else {}

        if isinstance(schedule, str):
            schedule = CronSchedule.from_expression(schedule, inputs)
        else:
            schedule.inputs |= inputs

        def _decorator(handler: Callable):
            self.functions.append(
                Function.from_handler(handler, kwargs, events=[schedule])
            )

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return _decorator

    def get(self, url: str, **kwargs: Unpack[FunctionKwargs]) -> Callable:
        """Define a routed handler which will respond to GET requests.

        :param url: relative url to trigger the function

        *Note:*
            - Requires an API gateway
        """
        kwargs |= {"url": url, "methods": [HTTPMethod.GET]}
        return self.func(**kwargs)

    def post(self, url: str, **kwargs: Unpack[FunctionKwargs]) -> Callable:
        """Define a routed handler which will respond to POST requests.

        :param url: relative url to trigger the function

        *Note:*
            - Requires an API gateway
        """
        kwargs |= {"url": url, "methods": [HTTPMethod.POST]}
        return self.func(**kwargs)

    def put(self, url: str, **kwargs: Unpack[FunctionKwargs]) -> Callable:
        """Define a routed handler which will respond to PUT requests.

        :param url: relative url to trigger the function

        *Note:*
            - Requires an API gateway
        """
        kwargs |= {"url": url, "methods": [HTTPMethod.PUT]}
        return self.func(**kwargs)

    def delete(self, url: str, **kwargs: Unpack[FunctionKwargs]) -> Callable:
        """Define a routed handler which will respond to DELETE requests.

        :param url: relative url to trigger the function

        *Note:*
            - Requires an API gateway
        """
        kwargs |= {"url": url, "methods": [HTTPMethod.DELETE]}
        return self.func(**kwargs)

    def patch(self, url: str, **kwargs: Unpack[FunctionKwargs]) -> Callable:
        """Define a routed handler which will respond to PATCH requests.

        :param url: relative url to trigger the function

        *Note:*
            - Requires an API gateway
        """
        kwargs |= {"url": url, "methods": [HTTPMethod.PATCH]}
        return self.func(**kwargs)
