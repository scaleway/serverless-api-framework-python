from dataclasses import dataclass
from enum import Enum
from typing import Optional

from scw_serverless.config.utils import _SerializableDataClass


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
class GatewayRoute(_SerializableDataClass):
    """Route to a function."""

    relative_url: str
    http_methods: Optional[list[HTTPMethod]] = None
    target: Optional[str] = None

    def validate(self) -> None:
        """Validates a route."""
        if not self.relative_url:
            raise RuntimeError("Route relative_url must be defined")
        if not self.target:
            raise RuntimeError("Route target must be defined")
