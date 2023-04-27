from dataclasses import dataclass, field
from typing import Callable, Literal, Optional, TypedDict

from scw_serverless.config.route import GatewayRoute, HTTPMethod
from scw_serverless.config.triggers import CronTrigger
from scw_serverless.utils.string import module_to_path, to_valid_function_name

MemoryLimit = Literal[128, 256, 512, 1024, 2048, 3072, 4096]
Privacy = Literal["private", "public"]  # Stricter than FunctionPrivacy from the SDK
HTTPOption = Literal["enabled", "redirected"]


class FunctionKwargs(TypedDict, total=False):
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
                        If "redirected" (default), allow http traffic to your function.
                        Blocked otherwise.

    .. seealso::

        `Scaleway Developers Documentation
        <https://developers.scaleway.com/en/products/functions/api/#create-a-function>`_
    """

    env: dict[str, str]
    secret: dict[str, str]
    min_scale: int
    max_scale: int
    memory_limit: MemoryLimit
    timeout: str
    custom_domains: list[str]
    privacy: Privacy
    description: str
    http_option: HTTPOption
    # Parameters for the Gateway
    relative_url: str
    http_methods: list[HTTPMethod]
    # Triggers
    triggers: list[CronTrigger]


# pylint: disable=too-many-instance-attributes
@dataclass
class Function:
    """Representation of a Scaleway function."""

    name: str
    handler: Callable
    handler_path: str
    environment_variables: Optional[dict[str, str]] = None
    min_scale: Optional[int] = None
    max_scale: Optional[int] = None
    memory_limit: Optional[int] = None
    timeout: Optional[str] = None
    secret_environment_variables: Optional[dict[str, str]] = None
    privacy: Privacy = "public"
    description: Optional[str] = None
    http_option: HTTPOption = "redirected"
    gateway_route: Optional[GatewayRoute] = None
    domains: list[str] = field(default_factory=list)
    triggers: list[CronTrigger] = field(default_factory=list)

    @staticmethod
    def from_handler(
        handler: Callable,
        args: FunctionKwargs,
    ):
        """Create a Scaleway function from a handler."""
        description = args.get("description")
        if not description and handler.__doc__:
            description = handler.__doc__
        gateway_route = None
        if url := args.get("relative_url"):
            gateway_route = GatewayRoute(url, http_methods=args.get("http_methods"))
        return Function(
            name=to_valid_function_name(handler.__name__),
            handler=handler,
            handler_path=module_to_path(handler.__module__) + "." + handler.__name__,
            environment_variables=args.get("env"),
            min_scale=args.get("min_scale"),
            max_scale=args.get("max_scale"),
            memory_limit=args.get("memory_limit"),
            timeout=args.get("timeout"),
            secret_environment_variables=args.get("secret"),
            privacy=args.get("privacy") or "public",
            description=description,
            http_option=args.get("http_option") or "redirected",
            gateway_route=gateway_route,
            domains=args.get("custom_domains") or [],
            triggers=args.get("triggers") or [],
        )
