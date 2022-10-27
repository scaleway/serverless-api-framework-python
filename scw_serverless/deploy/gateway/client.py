from typing import Optional

import dataclasses

import requests

from .models import GatewayInput, GatewayOutput

GATEWAY_CTRL_URL = "http://51.15.208.161"


class GatewayClient:
    def __init__(self, base_url: Optional[str] = None, *args, **kwargs):
        self.base_url: str = base_url if base_url else GATEWAY_CTRL_URL
        self.session: requests.Session = requests.Session(*args, **kwargs)
        self.session.headers.update(
            {"Content-type": "application/json", "Accept": "text/plain"}
        )

    def create_gateway(self, gateway: GatewayInput) -> GatewayOutput:
        res = self.session.post(
            f"{self.base_url}/gateways", json=dataclasses.asdict(gateway)
        )
        return GatewayOutput.from_dict(res.json())

    def get_gateway(self, uuid: str) -> GatewayOutput:
        res = self.session.get(f"{self.base_url}/gateways/{uuid}")
        return GatewayOutput.from_dict(res.json())

    def update_gateway(self, uuid: str, gateway: GatewayInput) -> GatewayOutput:
        res = self.session.put(
            f"{self.base_url}/gateways/{uuid}", json=dataclasses.asdict(gateway)
        )
        return GatewayOutput.from_dict(res.json())

    def delete_gateway(self, uuid: str):
        # Will raise on exceptions
        self.session.delete(f"{self.base_url}/gateways/{uuid}")
