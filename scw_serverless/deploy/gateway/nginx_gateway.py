import base64
import tempfile
from typing import TYPE_CHECKING

import scaleway.container.v1beta1 as sdk
from scaleway import Client
from scaleway.container.v1beta1 import ContainerV1Beta1API
from scaleway.function.v1beta1 import Function, FunctionV1Beta1API

from scw_serverless.logger import get_logger

from .nginx_config import generate_nginx_config

if TYPE_CHECKING:
    from scw_serverless.app import Serverless


class NginxGateway:
    """An Nginx-based API Gateway running on Scaleway containers."""

    def __init__(
        self,
        app_instance: "Serverless",
        sdk_client: Client,
    ):
        self.app_instance = app_instance
        self.container_api = ContainerV1Beta1API(sdk_client)
        self.function_api = FunctionV1Beta1API(sdk_client)
        self.logger = get_logger()

    def _list_created_functions(self) -> dict[str, Function]:
        """Gets the list of created functions."""
        namespace_name = self.app_instance.service_name
        namespaces = self.function_api.list_namespaces_all(name=namespace_name)
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
            for function in self.function_api.list_functions_all(
                namespace_id=namespace_id
            )
        }

    def _get_or_create_namespace(self) -> str:
        project_id = self.container_api.client.default_project_id
        namespace_name = f"{self.app_instance.service_name}-gateway"
        namespace = None
        self.logger.default(
            f"Looking for an existing namespace {namespace_name} in {project_id}..."
        )
        # Search in the user's namespace if one is matching the same name and region
        for deployed_namespace in self.container_api.list_namespaces_all():
            if deployed_namespace.name == namespace_name:
                namespace = deployed_namespace
        if not namespace:
            namespace = self.container_api.create_namespace(name=namespace_name)
            namespace = self.container_api.wait_for_namespace(namespace_id=namespace.id)
            if namespace.status != sdk.NamespaceStatus.READY:
                raise RuntimeError(
                    f"Namespace {namespace.name} has status {namespace.status}"
                    + (namespace.error_message or "")
                )
        return namespace.id

    def _get_or_create_container(
        self, namespace_id: str, nginx_config: str
    ) -> sdk.Container:
        container_name = "gateway"
        container = None
        for deployed_container in self.container_api.list_containers_all(
            namespace_id=namespace_id
        ):
            if deployed_container.name == container_name:
                container = deployed_container
        if container:
            self.logger.default(f"Updating gateway {container.id}...")
            container = self.container_api.update_container(
                container_id=container.id,
                privacy=sdk.ContainerPrivacy.PUBLIC,
                protocol=sdk.ContainerProtocol.HTTP1,
                secret_environment_variables=[
                    sdk.Secret("NGINX_CONF_B64", nginx_config)
                ],
                http_option=sdk.ContainerHttpOption.ENABLED,
                registry_image="rg.fr-par.scw.cloud/api-gateway-dev/gateway:latest",
                port=8080,
            )
        else:
            self.logger.default("Creating gateway...")
            container = self.container_api.create_container(
                name=container_name,
                namespace_id=namespace_id,
                privacy=sdk.ContainerPrivacy.PUBLIC,
                protocol=sdk.ContainerProtocol.HTTP1,
                secret_environment_variables=[
                    sdk.Secret("NGINX_CONF_B64", nginx_config)
                ],
                http_option=sdk.ContainerHttpOption.ENABLED,
                registry_image="rg.fr-par.scw.cloud/api-gateway-dev/gateway:latest",
                port=8080,
            )
        self.container_api.deploy_container(container_id=container.id)
        return self.container_api.wait_for_container(container_id=container.id)

    def deploy(self) -> None:
        """Deploy a self-hosted gateway."""

        created_functions = self._list_created_functions()
        for function in self.app_instance.functions:
            if not function.gateway_route:
                continue
            if function.name not in created_functions:
                raise RuntimeError(
                    f"Could not find function {function.name} in namespace"
                )
            # Configure the route to point to the function
            function.gateway_route.target = (
                "https://" + created_functions[function.name].domain_name
            )

        namespace_id = self._get_or_create_namespace()

        routes = [
            function.gateway_route
            for function in self.app_instance.functions
            if function.gateway_route
        ]

        nginx_config = generate_nginx_config(routes=routes)
        nginx_config = base64.b64encode(nginx_config.encode("utf-8"))

        container = self._get_or_create_container(
            namespace_id, nginx_config.decode("utf-8")
        )

        self.logger.success(f"Gateway deployed: https://{container.domain_name}")
