import os
from typing import Optional, List

from ...app import Serverless
from ...api import Api
from ..gateway.client import GatewayClient
from ..gateway.models import Route, GatewayInput, GatewayOutput


class GatewayController:
    def __init__(
        self,
        app_instance: Serverless,
        api: Api,
        gateway_uuid: Optional[str],
    ):
        self.gateway_uuid = gateway_uuid
        self.app_instance = app_instance
        self.api = api
        self.gateway_client = GatewayClient()

    def _get_routes(self) -> list[Route]:
        routes = []

        namespace_name = self.app_instance.service_name
        namespace_id = self.api.get_namespace_id(namespace_name)

        # Get the list of the deployed functions
        deployed_fns = {
            fn["name"]: fn for fn in self.api.list_functions(namespace_id=namespace_id)
        }
        # Compare with the configured functions
        for fn in self.app_instance.functions:
            if not fn.args.path:
                continue
            if not fn.name in deployed_fns:
                raise RuntimeError(
                    "could not find function %s in namespace %s"
                    % (fn.name, namespace_name)
                )

            deployed = deployed_fns[fn.name]
            routes.append(
                Route(
                    path=fn.args.path,
                    target=deployed["domain_name"],
                    methods=fn.args.methods,
                )
            )

        return routes

    def _deploy_to_existing(self, routes):
        self.logger.default(f"Updating gateway {self.gateway_uuid} configuration...")
        gateway = self.gateway_client.get_gateway(self.gateway_uuid)
        self.gateway_client.update_gateway(
            self.gateway_uuid, GatewayInput(gateway.domains, routes)
        )

    def _deploy_to_new(self, routes):
        self.logger.default("No gateway was configured, creating a new gateway...")
        out = self.gateway_client.create_gateway(gateway)
        self

    def manage_routes(self):
        routes = self._get_routes()

        if self.gateway_uuid:
            self._deploy_to_existing(routes)
        else:
            self._deploy_to_new(routes)
