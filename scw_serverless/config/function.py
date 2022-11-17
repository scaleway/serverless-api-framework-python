from typing import Callable, List, Literal, Optional, TypedDict

from typing_extensions import NotRequired

from scw_serverless.events.event import Event
from scw_serverless.utils.http import HTTPMethod
from scw_serverless.utils.string import module_to_path, to_valid_fn_name


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
    memory_limit: NotRequired[int]
    timeout: NotRequired[str]
    custom_domains: NotRequired[List[str]]
    privacy: NotRequired[Literal["private", "public"]]
    description: NotRequired[str]
    url: NotRequired[str]
    methods: NotRequired[list[HTTPMethod]]


class Function:
    """Representation of a Scaleway function."""

    def __init__(
        self,
        name: str,
        handler_path: str,
        args: FunctionKwargs,
        events: Optional[List[Event]] = None,
    ) -> None:
        self.name: str = to_valid_fn_name(name)
        self.handler_path: str = handler_path
        self.args: FunctionKwargs = args
        self.events: List[Event] = events if events else []

    @classmethod
    def from_handler(
        cls,
        handler: Callable,
        args: FunctionKwargs,
        events: Optional[List[Event]] = None,
    ):
        """Create a Scaleway function from a handler."""
        return cls(
            name=handler.__name__,
            handler_path=module_to_path(handler.__module__) + "." + handler.__name__,
            args=args,
            events=events,
        )

    def get_url(self) -> Optional[str]:
        """Get the function url if present."""
        return self.args.get("url")
