import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Literal, Optional, TypedDict

import scaleway.function.v1beta1 as sdk

if TYPE_CHECKING:
    try:
        from typing import NotRequired
    except ImportError:
        from typing_extensions import NotRequired
# pylint: disable=wrong-import-position # Conditional import considered a statement
from scw_serverless.config.route import GatewayRoute, HTTPMethod
from scw_serverless.config.utils import _SerializableDataClass
from scw_serverless.logger import get_logger
from scw_serverless.triggers import Trigger
from scw_serverless.utils.string import module_to_path, to_valid_fn_name

MemoryLimit = Literal[128, 256, 512, 1024, 2048, 3072, 4096]
Privacy = Literal["private", "public"]  # Stricter than FunctionPrivacy from the SDK
HTTPOption = Literal["enabled", "redirected"]


def _get_current_runtime() -> sdk.FunctionRuntime:
    runtime = sdk.FunctionRuntime.PYTHON310
    version = f"python{sys.version_info.major}{sys.version_info.minor}"
    try:
        runtime = sdk.FunctionRuntime(version)
    except ValueError:
        get_logger().warning(
            f"Unsupported Python version: {version}, selecting default: {runtime}"
        )
    return runtime


class FunctionKwargs(TypedDict):
    """Typed arguments supported by Scaleway functions.

    .. note::

        Some parameters may not be supported by a specific backend.

    :param env: Environment variables to be made available in your function.
    :param secret: Secret environment variables to be made available in your function.
    :param min_scale: Minimum replicas for your function.
    :param max_scale: Maximum replicas for your function.
    :param memory_limit: Memory (in MB) allocated to your function.
    :param timeout: Max duration to respond to a request.
    :param description: Description. Defaults to the function docstring if defined.
    :param http_option: Either "enabled" or "redirected".
                        If "redirected" (default), redirects http traffic to your function.
                        Blocked otherwise.
    .. seealso:: https://developers.scaleway.com/en/products/functions/api/#create-a-function

    """

    env: NotRequired[dict[str, str]]
    secret: NotRequired[dict[str, str]]
    min_scale: NotRequired[int]
    max_scale: NotRequired[int]
    memory_limit: NotRequired[MemoryLimit]
    timeout: NotRequired[str]
    custom_domains: NotRequired[List[str]]
    privacy: NotRequired[Privacy]
    description: NotRequired[str]
    http_option: NotRequired[HTTPOption]
    # Parameters for the Gateway
    url: NotRequired[str]
    methods: NotRequired[list[HTTPMethod]]
    # Triggers
    triggers: NotRequired[list[Trigger]]


# pylint: disable=too-many-instance-attributes
@dataclass
class Function(_SerializableDataClass):
    """Representation of a Scaleway function."""

    name: str
    handler: str  # Path to the handler
    runtime: sdk.FunctionRuntime
    environment_variables: Optional[dict[str, str]] = None
    min_scale: Optional[int] = None
    max_scale: Optional[int] = None
    memory_limit: Optional[int] = None
    timeout: Optional[str] = None
    secret_environment_variables: Optional[list[sdk.Secret]] = None
    privacy: Optional[sdk.FunctionPrivacy] = None
    description: Optional[str] = None
    http_option: Optional[sdk.FunctionHttpOption] = None
    gateway_route: Optional[GatewayRoute] = None
    domains: list[str] = field(default_factory=list)
    triggers: list[Trigger] = field(default_factory=list)

    @staticmethod
    def from_handler(
        handler: Callable,
        args: FunctionKwargs,
    ):
        """Create a Scaleway function from a handler."""
        description = args.get("description")
        if not description and handler.__doc__:
            description = handler.__doc__
        secrets = None
        if args_secret := args.get("secret"):
            secrets = [sdk.Secret(key, value) for key, value in args_secret.items()]
        privacy = None
        if args_privacy := args.get("privacy"):
            privacy = sdk.FunctionPrivacy(args_privacy)
        http_option = None
        if args_http_option := args.get("http_option"):
            http_option = sdk.FunctionHttpOption(args_http_option)
        gateway_route = None
        if url := args.get("url"):
            gateway_route = GatewayRoute(url, methods=args.get("methods"))

        return Function(
            name=to_valid_fn_name(handler.__name__),
            handler=module_to_path(handler.__module__) + "." + handler.__name__,
            environment_variables=args.get("env"),
            min_scale=args.get("min_scale"),
            max_scale=args.get("max_scale"),
            runtime=_get_current_runtime(),
            memory_limit=args.get("memory_limit"),
            timeout=args.get("timeout"),
            secret_environment_variables=secrets,
            privacy=privacy,
            description=description,
            http_option=http_option,
            gateway_route=gateway_route,
            domains=args.get("custom_domains") or [],
            triggers=args.get("triggers") or [],
        )

    def secrets_asdict(self) -> Optional[dict[str, str]]:
        """Gets secret_environment_variables as a dictionary"""
        if not self.secret_environment_variables:
            return None
        return {
            secret.key: (secret.value or "")
            for secret in self.secret_environment_variables
        }
