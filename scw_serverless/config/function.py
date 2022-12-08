import sys
from dataclasses import dataclass
from typing import Any, Callable, List, Literal, Optional, TypedDict

from scaleway.function.v1beta1.types import FunctionPrivacy, FunctionRuntime, Secret
from typing_extensions import NotRequired

from scw_serverless.config.route import GatewayRoute, HTTPMethod
from scw_serverless.config.utils import _SerializableDataClass
from scw_serverless.logger import get_logger
from scw_serverless.triggers import Trigger
from scw_serverless.utils.string import module_to_path, to_valid_fn_name

MemoryLimit = Literal[128, 256, 512, 1024, 2048, 3072, 4096]
Privacy = Literal["private", "public"]  # Stricter than FunctionPrivacy from the SDK


def _get_current_runtime() -> FunctionRuntime:
    runtime = FunctionRuntime.PYTHON310
    version = f"python{sys.version_info.major}{sys.version_info.minor}"
    try:
        runtime = FunctionRuntime(version)
    except ValueError:
        get_logger().warning(
            f"Unsupported Python version: {version}, selecting default: {runtime}"
        )
    return runtime


class FunctionKwargs(TypedDict):
    """
    Typed arguments supported by Scaleway functions.

    See also:
    https://developers.scaleway.com/en/products/functions/api/#create-a-function
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
    environment_variables: Optional[dict[str, str]]
    min_scale: Optional[int]
    max_scale: Optional[int]
    runtime: FunctionRuntime
    memory_limit: Optional[int]
    timeout: Optional[str]
    secret_environment_variables: Optional[list[Secret]]
    privacy: Optional[FunctionPrivacy]
    description: Optional[str]

    gateway_route: Optional[GatewayRoute]
    domains: list[str]
    triggers: list[Trigger]

    @staticmethod
    def from_handler(
        handler: Callable,
        args: FunctionKwargs,
    ):
        """Create a Scaleway function from a handler."""
        description = args.get("description")
        if not description and handler.__doc__:
            description = handler.__doc__
        privacy = None
        if args_privacy := args.get("privacy"):
            privacy = FunctionPrivacy(args_privacy)
        gateway_route = None
        if url := args.get("url"):
            gateway_route = GatewayRoute(url, methods=args.get("methods"))
        secrets = None
        if args_secret := args.get("secret"):
            secrets = [Secret(key, value) for key, value in args_secret.items()]

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
            gateway_route=gateway_route,
            domains=args.get("custom_domains") or [],
            triggers=args.get("triggers") or [],
        )

    def asdict(self) -> dict[str, Any]:
        """Converts to a dictionary compatible with the SDK."""
        result = super().asdict()
        reject_keys = ["gateway_route", "domains", "triggers"]
        result = {k: v for k, v in result.items() if k not in reject_keys}
        if "privacy" not in result:  # Privacy is required by the SDK
            result["privacy"] = "public"
        return result

    def secrets_asdict(self) -> Optional[dict[str, str]]:
        """Gets secret_environment_variables as a dictionary"""
        if not self.secret_environment_variables:
            return None
        return {
            secret.key: (secret.value or "")
            for secret in self.secret_environment_variables
        }
