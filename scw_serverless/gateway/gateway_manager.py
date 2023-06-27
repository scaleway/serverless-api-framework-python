from typing import Protocol

import scaleway.function.v1beta1 as sdk
from scaleway import Client

from scw_serverless.app import Serverless
from scw_serverless.config.route import GatewayRoute


class Gateway(Protocol):
    """Generic Gateway Implementation."""

    def add_route(self, route: GatewayRoute) -> None:
        """Add a route to the Gateway."""


class GatewayManager:
    """Apply the configured routes to an existing API Gateway."""

    def __init__(
        self,
        app_instance: Serverless,
        gateway: Gateway,
        sdk_client: Client,
    ):
        self.app_instance = app_instance
        self.api = sdk.FunctionV1Beta1API(sdk_client)
        self.gateway = gateway

    def _list_created_functions(self) -> dict[str, sdk.Function]:
        """Get the list of created functions."""
        namespace_name = self.app_instance.service_name
        namespaces = self.api.list_namespaces_all(name=namespace_name)
        if not namespaces:
            raise RuntimeError(
                f"Could not find a namespace with name: {namespace_name}"
            )
        if len(namespaces) > 1:
            namespaces_ids = ", ".join([ns.id for ns in namespaces])
            raise RuntimeWarning(
                f"Foud multiple namespaces with name {namespace_name}: {namespaces_ids}"
            )

        namespace_id = namespaces[0].id
        return {
            function.name: function
            for function in self.api.list_functions_all(namespace_id=namespace_id)
        }

    def update_routes(self) -> None:
        """Update the Gateway routes configured by the functions."""
        created_functions = self._list_created_functions()
        routed_functions = [
            function
            for function in self.app_instance.functions
            if function.gateway_route
        ]

        for function in routed_functions:
            if function.name not in created_functions:
                raise RuntimeError(
                    f"Could not update route to function {function.name} "
                    + "because it was not deployed"
                )

            target = "https://" + created_functions[function.name].domain_name
            function.gateway_route.target = target  # type: ignore

        for function in routed_functions:
            self.gateway.add_route(function.gateway_route)  # type: ignore
