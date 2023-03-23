import requests

from scw_serverless.config.route import GatewayRoute


class GatewayAPIClient:
    """A client for the API to manage routes on the Gateway."""

    def __init__(self, gateway_url: str, gateway_api_key: str):
        self.url = gateway_url + "/scw"

        self.session = requests.Session()
        self.session.headers["X-Auth-Token"] = gateway_api_key

    def get_all(self) -> list[GatewayRoute]:
        """Get all previously defined routes."""

        resp = self.session.get(self.url)
        resp.raise_for_status()

        endpoints = resp.json()["endpoints"]
        routes = []
        for endpoint in endpoints:
            routes.append(
                GatewayRoute(
                    relative_url=endpoint["relative_url"],
                    http_methods=endpoint.get("http_methods"),
                    target=endpoint["target"],
                )
            )

        return routes

    def create_route(self, route: GatewayRoute) -> None:
        """Create a route on the API Gateway."""

        route.validate()

        resp = self.session.post(self.url, json=route.asdict())
        resp.raise_for_status()

    def delete_route(self, route: GatewayRoute) -> None:
        """Delete a route on the API Gateway."""

        resp = self.session.delete(self.url, json=route.asdict())
        resp.raise_for_status()
