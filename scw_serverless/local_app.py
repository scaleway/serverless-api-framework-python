from typing import Any, Callable

from scaleway_functions_python import local

from scw_serverless.app import Serverless
from scw_serverless.config.function import FunctionKwargs

try:
    from typing import Unpack
except ImportError:
    from typing_extensions import Unpack
# pylint: disable=wrong-import-position # Conditional import considered a statement


class ServerlessLocal(Serverless):
    """Serverless class that is used when testing locally.

    Crate a local testing framework server and inject the handlers to it.
    """

    def __init__(
        self,
        service_name: str,
        env: dict[str, Any] | None = None,
        secret: dict[str, Any] | None = None,
    ):
        super().__init__(service_name, env, secret)
        self.local_server = local.LocalFunctionServer()

    def func(
        self,
        **kwargs: "Unpack[FunctionKwargs]",
    ) -> Callable:
        decorator = super().func(**kwargs)

        def _decorator(handler: Callable):
            decorator(handler)
            http_methods = None
            if methods := kwargs.get("http_methods"):
                http_methods = [method.value for method in methods]
            self.local_server.add_handler(
                handler=handler,
                relative_url=kwargs.get("relative_url"),
                http_methods=http_methods,
            )

        return _decorator
