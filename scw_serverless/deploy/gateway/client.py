import dataclasses

import requests

from scw_serverless.deploy.gateway.models import GatewayInput, GatewayOutput


class GatewayClient:
    """Client for the API to manage gateways."""

    def __init__(self, base_url: str, *args, **kwargs):
        self.base_url: str = base_url
        self.gateways_base_url: str = f"{self.base_url}/gateways"
        self.session: requests.Session = requests.Session(*args, **kwargs)
        self.session.headers.update(
            {"Content-type": "application/json", "Accept": "text/plain"}
        )

    def create_gateway(self, gateway: GatewayInput) -> GatewayOutput:
        """Creates a gateway."""
        res = self.session.post(
            self.gateways_base_url, json=dataclasses.asdict(gateway)
        )
        return GatewayOutput.from_dict(res.json())

    def get_gateway(self, uuid: str) -> GatewayOutput:
        """Gets details on a gateway."""
        res = self.session.get(f"{self.gateways_base_url}/{uuid}")
        return GatewayOutput.from_dict(res.json())

    def update_gateway(self, uuid: str, gateway: GatewayInput) -> GatewayOutput:
        """Updates a gateway."""
        res = self.session.put(
            f"{self.gateways_base_url}/{uuid}", json=dataclasses.asdict(gateway)
        )
        return GatewayOutput.from_dict(res.json())

    def delete_gateway(self, uuid: str) -> None:
        """Deletes a gateway.

        Note: raises if status is not OK
        """
        res = self.session.delete(f"{self.gateways_base_url}/{uuid}")
        res.raise_for_status()
