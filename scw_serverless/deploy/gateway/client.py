import urllib
from typing import Optional

import requests

import models


GATEWAY_CTRL_URL = "51.15.208.161"


class GatewayClient:
    def __init__(self, base_url: Optional[str], *args, **kwargs):
        self.base_url: str = base_url if base_url else GATEWAY_CTRL_URL
        self.session: requests.Session = requests.Session(*args, **kwargs)

    def create_gateway(self, gateway: models.GatewayInput) -> models.GatewayOutput:
        res = self.session.post(f"{self.base_url}/gateways", json=gateway)
        return models.GatewayOutput.from_dict(res)

    def get_gateway(self, uuid: str) -> models.GatewayOutput:
        res = self.session.get(f"{self.base_url}/gateways/{self.uuid}")
        return models.GatewayOutput.from_dict(res)

    def update_gateway(
        self, uuid: str, gateway: models.GatewayInput
    ) -> models.GatewayOutput:
        res = self.session.put(f"{self.base_url}/gateways/{self.uuid}", json=gateway)
        return models.GatewayOutput.from_dict(res)

    def delete_gateway(self, uuid: str):
        # Will raise on exceptions
        self.session.delete(f"{self.base_url}/gateways/{self.uuid}")
