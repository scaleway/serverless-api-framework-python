import os
from typing import Tuple

import requests
import scaleway.function.v1beta1 as sdk
from scaleway import Client
from scaleway.core.utils.waiter import WaitForOptions

from scw_serverless.app import Serverless
from scw_serverless.config.function import Function
from scw_serverless.deploy.backends.serverless_backend import ServerlessBackend
from scw_serverless.utils.files import create_zip_file

TEMP_DIR = "./.scw"
DEPLOYMENT_ZIP = f"{TEMP_DIR}/deployment.zip"
UPLOAD_TIMEOUT = 600  # In seconds
DEPLOY_TIMEOUT = 600


class ScalewayApiBackend(ServerlessBackend):
    """Uses the API to deploy functions."""

    def __init__(
        self, app_instance: Serverless, sdk_client: Client, single_source: bool
    ):
        super().__init__(app_instance, sdk_client)
        self.single_source = single_source
        self.api = sdk.FunctionV1Beta1API(sdk_client)

    def _get_or_create_function(
        self, function: Function, namespace_id: str
    ) -> Tuple[str, str]:
        self.logger.default(f"Looking for an existing function {function.name}...")
        created_function = None
        # Looking if a function is already existing
        for func in self.api.list_functions_all(namespace_id):
            if func.name == function.name:
                created_function = func
        if not created_function:
            self.logger.default(f"Creating a new function {function.name}...")
            # Creating a new function with the provided args
            created_function = self.api.create_function(
                namespace_id=namespace_id,
                # required by the SDK
                http_option=sdk.FunctionHttpOption.UNKNOWN_HTTP_OPTION,
                **function.asdict(),
            )
        else:
            # Updating the function with the provided args
            kwargs = function.asdict()
            del kwargs["name"]
            created_function = self.api.update_function(
                function_id=created_function.id,
                # required by the SDK
                http_option=sdk.FunctionHttpOption.UNKNOWN_HTTP_OPTION,
                **kwargs,
            )
        return (created_function.id, created_function.domain_name)

    def _deploy_function(self, function: Function, namespace_id: str, zip_size: int):
        function_id, domain_name = self._get_or_create_function(function, namespace_id)

        # Get an object storage pre-signed url
        try:
            upload_url = self.api.get_function_upload_url(
                function_id=function_id, content_length=zip_size
            ).url
        except Exception as exception:
            self.logger.error(
                "Unable to retrieve upload url... "
                + "Verify that your function is less that 100 MB"
            )
            raise exception

        self.logger.default("Uploading function...")
        with open(DEPLOYMENT_ZIP, mode="rb") as file:
            # Upload function zip to S3 presigned URL
            req = requests.put(
                upload_url,
                data=file,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(zip_size),
                },
                timeout=UPLOAD_TIMEOUT,
            )

            if req.status_code != 200:
                raise RuntimeError("Unable to upload function code... Aborting...")

        self.logger.default("Deploying function...")
        # deploy the newly uploaded function
        self.api.deploy_function(function_id)

        func = self.api.wait_for_function(
            function_id,
            options=WaitForOptions(
                timeout=DEPLOY_TIMEOUT,
                min_delay=10,
                stop=lambda f: (
                    f.status in [sdk.FunctionStatus.READY, sdk.FunctionStatus.ERROR]
                ),
            ),
        )
        if func.status is sdk.FunctionStatus.ERROR:
            raise ValueError(
                f"Function {func.name} is in error state: {func.error_message}"
            )
        self.logger.success(f"Function {func.name} deployed to: https://{domain_name}")

    def _create_deployment_zip(self):
        # Create a ZIP archive containing the entire project
        self.logger.default("Creating a deployment archive...")
        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)

        if os.path.exists(DEPLOYMENT_ZIP):
            os.remove(DEPLOYMENT_ZIP)

        create_zip_file(DEPLOYMENT_ZIP, "./")
        return os.path.getsize(DEPLOYMENT_ZIP)

    def _remove_missing_functions(self, namespace_id: str):
        """Deletes functions no longer present in the code."""
        function_names = [func.name for func in self.app_instance.functions]
        for func in self.api.list_functions_all(namespace_id=namespace_id):
            if func.name not in function_names:
                self.logger.info(f"Deleting function {func.name}...")
                self.api.delete_function(func.id)

    def _get_or_create_namespace(self) -> str:
        project_id = self.api.client.default_project_id
        namespace_name = self.app_instance.service_name
        namespace = None
        self.logger.default(
            f"Looking for an existing namespace {namespace_name} in {project_id}..."
        )
        # Search in the user's namespace if one is matching the same name and region
        for deployed_namespace in self.api.list_namespaces_all():
            if deployed_namespace.name == self.app_instance.service_name:
                namespace = deployed_namespace
        self.logger.default(
            f"Creating a new namespace {namespace_name} in {project_id}..."
        )
        secrets = [
            sdk.Secret(key, value)
            for key, value in (self.app_instance.secret or {}).items()
        ]
        if not namespace:
            # Create a new namespace
            namespace = self.api.create_namespace(
                name=namespace_name,
                environment_variables=self.app_instance.env,
                secret_environment_variables=secrets,
            )
        else:
            self.logger.default("Updating namespace configuration...")
            namespace = self.api.update_namespace(
                namespace_id=namespace.id,
                environment_variables=self.app_instance.env,
                secret_environment_variables=secrets,
            )
        namespace = self.api.wait_for_namespace(
            namespace_id=namespace.id,
            options=WaitForOptions(
                stop=lambda namespace: namespace.status != sdk.NamespaceStatus.PENDING
            ),
        )
        if namespace.status != sdk.NamespaceStatus.READY:
            raise ValueError(
                f"Namespace {namespace.name} is not ready: {namespace.error_message}"
            )
        return namespace.id

    def deploy(self) -> None:
        namespace_id = self._get_or_create_namespace()
        # Create a zip containing the user's project
        file_size = self._create_deployment_zip()

        # For each function
        for function in self.app_instance.functions:
            # Deploy the function
            self._deploy_function(function, namespace_id, zip_size=file_size)

        if self.single_source:
            # Remove functions no longer present in the code
            self._remove_missing_functions(namespace_id)

        self.logger.success("Done! Functions have been successfully deployed!")
