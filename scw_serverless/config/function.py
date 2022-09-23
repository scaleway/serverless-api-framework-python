import imp
from typing import Any, List, Callable, TypedDict, Literal
from typing_extensions import NotRequired

from ..utils import module_to_path
from ..events.event import Event


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


class Function:
    def __init__(
        self,
        name: str,
        handler_path: str,
        args: FunctionKwargs,
        events: List[Event] = [],
    ) -> None:
        self.name: str = name
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
