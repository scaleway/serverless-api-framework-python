from typing import List, Callable, TypedDict, Literal, Optional, Any

from typing_extensions import NotRequired

from scw_serverless.utils.http import HTTPMethod
from scw_serverless.events.event import Event
from scw_serverless.utils.string import module_to_path, to_valid_fn_name


class FunctionKwargs(TypedDict):
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
    def __init__(
        self,
        name: str,
        handler_path: str,
        args: FunctionKwargs,
        events: List[Event] = [],
    ) -> None:
        self.name: str = to_valid_fn_name(name)
        self.handler_path: str = handler_path
        self.args: FunctionKwargs = args
        self.events: List[Event] = events

    @classmethod
    def from_handler(
        Func, handler: Callable, args: FunctionKwargs, events: List[Event] = []
    ):
        return Func(
            name=handler.__name__,
            handler_path=module_to_path(handler.__module__) + "." + handler.__name__,
            args=args,
            events=events,
        )

    def get_url(self) -> Optional[str]:
        """Get the function url if present."""
        return self.args.get("url")
