from dataclasses import dataclass
from enum import Enum
from typing import Optional


class HTTPMethod(Enum):
    """Enum of supported HTTP methods.

    See also: https://docs.python.org/3/library/http.html#http.HTTPMethod
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
