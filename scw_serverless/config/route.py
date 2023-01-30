import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class HTTPMethod(Enum):
    """Enum of supported HTTP methods.

    .. seealso:: https://docs.python.org/3/library/http.html#http.HTTPMethod
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class GatewayRoute:
    """Route to a function."""

    path: str
    methods: Optional[list[HTTPMethod]] = None
    target: Optional[str] = None

    def validate(self) -> None:
        """Validates the route."""
        if self.path == "":
            raise ValueError("No path specified")
        if not re.match(r"[A-Za-z0-9:.]*[\/]{1}.*\/?$", self.path):
            raise ValueError(f"Invalid path: {self.path}")
        for method in self.methods or []:
            if method not in HTTPMethod:
                raise ValueError(f"Unsupported method: {method}")
