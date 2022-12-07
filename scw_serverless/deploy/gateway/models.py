from dataclasses import dataclass
from typing import Any


@dataclass
class Route:
    """Represents a Gateway Route from path to target with methods."""

    path: str
    target: str
    methods: list[str]

    @staticmethod
    def from_dict(data: dict[str, Any]):
        """Converts from a dict."""
        return Route(path=data["path"], target=data["target"], methods=data["methods"])


@dataclass
class GatewayOutput:
    """Represents a Gateway returned from the API."""

    uuid: str
    domains: list[str]
    routes: list[Route]

    @staticmethod
    def from_dict(data: dict[str, Any]):
        """Converts from a dict."""
        routes = [Route.from_dict(route) for route in data["routes"]]
        return GatewayOutput(uuid=data["uuid"], domains=data["domains"], routes=routes)


@dataclass
class GatewayInput:
    """Represents a Gateway creation request to the API."""

    domains: list[str]
    routes: list[Route]
