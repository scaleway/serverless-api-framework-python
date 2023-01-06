from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

if TYPE_CHECKING:
    try:
        from typing import Unpack
    except ImportError:
        from typing_extensions import Unpack
# pylint: disable=wrong-import-position # Conditional import considered a statement
from scw_serverless.config.function import Function, FunctionKwargs
from scw_serverless.config.route import HTTPMethod
from scw_serverless.triggers import CronTrigger


class Serverless:
    """Manage your Serverless Functions.

    :param service_name: name of the namespace
    :param env: namespace level environment variables
    :param secret: namespace level secrets
    :param gateway_domains: domains to be supported by the gatewas
    """

    def __init__(
        self,
        service_name: str,
        env: Optional[dict[str, Any]] = None,
        secret: Optional[dict[str, Any]] = None,
        gateway_domains: Optional[list[str]] = None,
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
        schedule: Union[str, CronTrigger],
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: Unpack[FunctionKwargs],
    ) -> Callable:
        """Define a scheduled handler with Cron, passing inputs as parameters.

        :param schedule: Cron schedule to run with
        :param inputs: parameters to be passed to the body
        """
        if isinstance(schedule, str):
            schedule = CronTrigger(schedule, inputs)
        elif inputs:
            schedule.args = (schedule.args or {}) | inputs
        if "triggers" in kwargs and kwargs["triggers"]:
            kwargs["triggers"].append(schedule)
        else:
            kwargs |= {"triggers": [schedule]}
        return self.func(**kwargs)

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
