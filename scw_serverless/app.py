from typing import TYPE_CHECKING, Any, Callable, Optional, Union

if TYPE_CHECKING:
    try:
        from typing import Unpack
    except ImportError:
        from typing_extensions import Unpack
    # pylint: disable=wrong-import-position # Conditional import considered a statement

from scw_serverless.config import triggers
from scw_serverless.config.function import Function, FunctionKwargs
from scw_serverless.config.route import HTTPMethod


class Serverless:
    """Manage your Serverless Functions.

    Maps to a function namespace. Parameters will be scoped to the namespace.

    :param service_name: name of the namespace
    :param env: namespace level environment variables
    :param secret: namespace level secrets
    """

    def __init__(
        self,
        service_name: str,
        env: Optional[dict[str, Any]] = None,
        secret: Optional[dict[str, Any]] = None,
    ):
        self.functions: list[Function] = []
        self.service_name: str = service_name
        self.env = env
        self.secret = secret

    def func(
        self,
        **kwargs: "Unpack[FunctionKwargs]",
    ) -> Callable:
        """Define a Serverless handler and its parameters from the keyword arguments.

        See :any:`FunctionKwargs` for all possible parameters.

        Example
        -------

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

            return handler

        return _decorator

    def schedule(
        self,
        schedule: Union[str, triggers.CronTrigger],
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: "Unpack[FunctionKwargs]",
    ) -> Callable:
        """Define a scheduled handler with Cron, passing inputs as parameters.

        :param schedule: cron schedule to use
        :param inputs: parameters to be passed to the body

        Example
        -------

        .. code-block:: python

            app.schedule(schedule="5 4 * * sun", inputs={"foo": "bar"}, memory=1024)
            def handler(event, context)
                ...
        """
        if isinstance(schedule, str):
            schedule = triggers.CronTrigger(schedule, inputs)
        elif inputs:
            schedule.args = (schedule.args or {}) | inputs
        if "triggers" in kwargs and kwargs["triggers"]:
            kwargs["triggers"].append(schedule)
        else:
            kwargs["triggers"] = [schedule]
        return self.func(**kwargs)

    def get(self, url: str, **kwargs: "Unpack[FunctionKwargs]") -> Callable:
        """Define a routed handler which will respond to GET requests.

        :param url: relative url to trigger the function

        .. note::

            Requires an API gateway

            For more information, please consult the :doc:`gateway` page.
        """
        kwargs |= {"relative_url": url, "http_methods": [HTTPMethod.GET]}
        return self.func(**kwargs)

    def post(self, url: str, **kwargs: "Unpack[FunctionKwargs]") -> Callable:
        """Define a routed handler which will respond to POST requests.

        :param url: relative url to trigger the function

        .. note::
            Requires an API gateway

            For more information, please consult the :doc:`gateway` page.
        """
        kwargs |= {"relative_url": url, "http_methods": [HTTPMethod.POST]}
        return self.func(**kwargs)

    def put(self, url: str, **kwargs: "Unpack[FunctionKwargs]") -> Callable:
        """Define a routed handler which will respond to PUT requests.

        :param url: relative url to trigger the function

        .. note::

            Requires an API gateway

            For more information, please consult the :doc:`gateway` page.
        """
        kwargs |= {"relative_url": url, "http_methods": [HTTPMethod.PUT]}
        return self.func(**kwargs)

    def delete(self, url: str, **kwargs: "Unpack[FunctionKwargs]") -> Callable:
        """Define a routed handler which will respond to DELETE requests.

        :param url: relative url to trigger the function

        .. note::

            Requires an API gateway

            For more information, please consult the :doc:`gateway` page.
        """
        kwargs |= {"relative_url": url, "http_methods": [HTTPMethod.DELETE]}
        return self.func(**kwargs)

    def patch(self, url: str, **kwargs: "Unpack[FunctionKwargs]") -> Callable:
        """Define a routed handler which will respond to PATCH requests.

        :param url: relative url to trigger the function

        .. note::

            Requires an API gateway

            For more information, please consult the :doc:`gateway` page.
        """
        kwargs |= {"relative_url": url, "http_methods": [HTTPMethod.PATCH]}
        return self.func(**kwargs)
