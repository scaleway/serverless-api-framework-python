from typing import Optional

import scaleway.function.v1beta1 as sdk
from scaleway import Client

from scw_serverless.app import Serverless
from scw_serverless.deploy.gateway.client import GatewayClient
from scw_serverless.deploy.gateway.models import GatewayInput, Route
from scw_serverless.logger import get_logger


class GatewayManager:
    """Manages API Gateways."""

    def __init__(
        self,
        app_instance: Serverless,
        sdk_client: Client,
        gateway_uuid: Optional[str],
        gateway_client: GatewayClient,
    ):

        self.api = sdk.FunctionV1Beta1API(sdk_client)
        self.app_instance = app_instance
        self.gateway_client = gateway_client
        self.gateway_uuid = gateway_uuid
        self.logger = get_logger()

    def _get_routes(self, deployed_fns: dict[str, sdk.Function]) -> list[Route]:
        routes = []
        # Compare with the configured functions
        for function in self.app_instance.functions:
            if not function.gateway_route:
                continue
            if function.name not in deployed_fns:
                raise RuntimeError(
                    f"Could not find function {function.name} in namespace"
                )
            deployed = deployed_fns[function.name]
            routes.append(
                Route(
                    path=function.gateway_route.path,
                    target=deployed.domain_name,
                    methods=[
                        str(method) for method in function.gateway_route.methods or []
                    ],
                )
            )
        return routes

    def _list_deployed_fns(self) -> dict[str, sdk.Function]:
        namespace_name = self.app_instance.service_name
        namespaces = self.api.list_namespaces_all(name=namespace_name)
        if not namespaces:
            raise ValueError(f"Could not find a namespace with name: {namespace_name}")
        namespace_id = namespaces[0].id
        # Get the list of the deployed functions
        return {
            function.name: function
            for function in self.api.list_functions_all(namespace_id=namespace_id)
        }

    def _deploy_to_existing(self, routes: list[Route]) -> list[str]:
        assert self.gateway_uuid
        self.logger.default(f"Updating gateway {self.gateway_uuid} configuration...")
        gateway = self.gateway_client.get_gateway(self.gateway_uuid)
        domains = sorted(set(self.app_instance.gateway_domains + gateway.domains))
        self.gateway_client.update_gateway(
            self.gateway_uuid, GatewayInput(domains, routes)
        )
        return domains

    def _deploy_to_new(self, routes: list[Route]) -> list[str]:
        self.logger.default("No gateway was configured, creating a new gateway...")
        gateway = self.gateway_client.create_gateway(
            GatewayInput(self.app_instance.gateway_domains, routes)
        )
        self.logger.success(f"Successfully created gateway {gateway.uuid}")
        return self.app_instance.gateway_domains

    def _display_routes(self, domains: list[str]):
        prefix = domains[0] if domains else ""
        routed = filter(
            lambda function: function.gateway_route, self.app_instance.functions
        )
        self.logger.default("The following functions were configured: ")
        for function in routed:
            assert function.gateway_route
            methods = ",".join(
                [str(method) for method in function.gateway_route.methods or []]
            )
            row = f"\t{function.name} on {prefix + function.gateway_route.path}"
            if methods:
                row += " with " + methods
            self.logger.default(row)

    def update_gateway_routes(self) -> None:
        """Updates the configurations of the API gateway."""

        deployed_fns = self._list_deployed_fns()
        routes = self._get_routes(deployed_fns)

        domains = None
        if self.gateway_uuid:
            domains = self._deploy_to_existing(routes)
        else:
            domains = self._deploy_to_new(routes)

        self._display_routes(domains)
