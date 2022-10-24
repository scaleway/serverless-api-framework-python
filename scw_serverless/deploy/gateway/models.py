from dataclasses import dataclass


@dataclass
class Route:
    path: str
    target: str
    methods: list[str]

    @staticmethod
    def from_dict(data):
        return Route(
            path=route["path"], target=route["target"], methods=route["methods"]
        )


@dataclass
class GatewayOutput:
    uuid: str
    domains: list[str]
    routes: list[Route]

    @staticmethod
    def from_dict(data):
        routes = [Route.from_dict(route) for route in data["routes"]]
        return GatewayOutput(uuid=data["uuid"], domains=data["domains"], routes=routes)


@dataclass
class GatewayInput:
    domains: list[str]
    routes: list[Route]
