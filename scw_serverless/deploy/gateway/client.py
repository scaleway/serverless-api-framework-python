import dataclasses
from typing import Optional

import requests

from .models import GatewayInput, GatewayOutput


class GatewayClient:
    def __init__(self, base_url: str, *args, **kwargs):
        self.base_url: str = base_url
        self.gateways_base_url: str = f"{self.base_url}/gateways"
        self.session: requests.Session = requests.Session(*args, **kwargs)
        self.session.headers.update(
            {"Content-type": "application/json", "Accept": "text/plain"}
        )

    def create_gateway(self, gateway: GatewayInput) -> GatewayOutput:
        res = self.session.post(
            self.gateways_base_url, json=dataclasses.asdict(gateway)
        )
        return GatewayOutput.from_dict(res.json())

    def get_gateway(self, uuid: str) -> GatewayOutput:
        res = self.session.get(f"{self.gateways_base_url}/{uuid}")
        return GatewayOutput.from_dict(res.json())

    def update_gateway(self, uuid: str, gateway: GatewayInput) -> GatewayOutput:
        res = self.session.put(
            f"{self.gateways_base_url}/{uuid}", json=dataclasses.asdict(gateway)
        )
        return GatewayOutput.from_dict(res.json())

    def delete_gateway(self, uuid: str):
        # Will raise on exceptions
        res = self.session.delete(f"{self.gateways_base_url}/{uuid}")
        res.raise_for_status()
