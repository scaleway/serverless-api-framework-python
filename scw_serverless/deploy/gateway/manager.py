from typing import Optional, Any

from ...logger import get_logger
from ...app import Serverless
from ...api import Api
from ..gateway.client import GatewayClient
from ..gateway.models import Route, GatewayInput


class GatewayManager:
    def __init__(
        self,
        app_instance: Serverless,
        api: Api,
        project_id: str,
        gateway_uuid: Optional[str],
        gateway_client: GatewayClient,
    ):
        self.app_instance = app_instance
        self.api = api
        self.project_id = project_id
        self.gateway_uuid = gateway_uuid
        self.gateway_client = gateway_client
        self.logger = get_logger()

    def _get_routes(self, deployed_fns: dict[str, Any]) -> list[Route]:
        routes = []

        # Compare with the configured functions
        for fn in self.app_instance.functions:
            if not fn.get("path"):
                continue
            if not fn.name in deployed_fns:
                raise RuntimeError(f"could not find function {fn.name} in namespace")

            deployed = deployed_fns[fn.name]
            routes.append(
                Route(
                    path=fn.get("path"),
                    target=deployed["domain_name"],
                    methods=fn.get("methods"),
                )
            )

        return routes

    def _list_deployed_fns(self) -> dict[str, Any]:
        namespace_name = self.app_instance.service_name
        namespace_id = self.api.get_namespace_id(self.project_id, namespace_name)

        # Get the list of the deployed functions
        return {
            fn["name"]: fn for fn in self.api.list_functions(namespace_id=namespace_id)
        }

    def _deploy_to_existing(self, routes):
        self.logger.default(f"Updating gateway {self.gateway_uuid} configuration...")
        gateway = self.gateway_client.get_gateway(self.gateway_uuid)
        domains = set(self.app_instance.gateway_domains + gateway.domains)
        self.gateway_client.update_gateway(
            self.gateway_uuid, GatewayInput(domains, routes)
        )

    def _deploy_to_new(self, routes):
        self.logger.default("No gateway was configured, creating a new gateway...")
        gateway = self.gateway_client.create_gateway(
            GatewayInput(self.app_instance.gateway_domains, routes)
        )
        self.logger.success(f"Successfully created gateway {gateway.uuid}")

    def update_gateway_routes(self):
        deployed_fns = self._list_deployed_fns()
        routes = self._get_routes(deployed_fns)

        if self.gateway_uuid:
            self._deploy_to_existing(routes)
        else:
            self._deploy_to_new(routes)
