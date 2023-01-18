import multiprocessing
import os

import requests
import scaleway.function.v1beta1 as sdk
from scaleway import Client
from scaleway_core.utils import WaitForOptions

from scw_serverless.app import Serverless
from scw_serverless.config.function import Function
from scw_serverless.deploy.backends.serverless_backend import ServerlessBackend
from scw_serverless.triggers import Trigger
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

    def _get_or_create_function(self, function: Function, namespace_id: str) -> str:
        self.logger.default(f"Looking for an existing function {function.name}...")
        created_function = None
        # Checking if a function already exists
        for func in self.api.list_functions_all(namespace_id=namespace_id):
            if func.name == function.name:
                created_function = func
        if not created_function:
            self.logger.default(f"Creating a new function {function.name}...")
            # Creating a new function with the provided args
            created_function = self.api.create_function(
                namespace_id=namespace_id,
                runtime=function.runtime,
                privacy=function.privacy or sdk.FunctionPrivacy.PUBLIC,
                http_option=sdk.FunctionHttpOption.REDIRECTED,
                name=function.name,
                environment_variables=function.environment_variables,
                min_scale=function.min_scale,
                max_scale=function.max_scale,
                memory_limit=function.memory_limit,
                timeout=function.timeout,
                handler=function.handler,
                description=function.description,
                secret_environment_variables=function.secret_environment_variables,
            )
        else:
            # Updating the function with the provided args
            created_function = self.api.update_function(
                function_id=created_function.id,
                runtime=function.runtime,
                privacy=function.privacy or sdk.FunctionPrivacy.PUBLIC,
                http_option=sdk.FunctionHttpOption.REDIRECTED,
                environment_variables=function.environment_variables,
                min_scale=function.min_scale,
                max_scale=function.max_scale,
                memory_limit=function.memory_limit,
                timeout=function.timeout,
                handler=function.handler,
                description=function.description,
                secret_environment_variables=function.secret_environment_variables,
            )
        return created_function.id

    def _deploy_function(
        self, function: Function, namespace_id: str, zip_size: int
    ) -> sdk.Function:
        function_id = self._get_or_create_function(function, namespace_id)

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

        self.logger.default(f"Uploading function {function.name}...")
        self._upload_deployment_zip(upload_url, zip_size)

        self.logger.default(f"Deploying function {function.name}...")
        # deploy the newly uploaded function
        self.api.deploy_function(function_id=function_id)

        return self.api.wait_for_function(
            function_id=function_id,
            options=WaitForOptions(
                timeout=DEPLOY_TIMEOUT,
                stop=lambda f: (f.status != sdk.FunctionStatus.PENDING),
            ),
        )

    def _deploy_trigger(self, function_id: str, trigger: Trigger) -> sdk.Cron:
        created_trigger = None
        # Checking if a trigger already exists
        for cron in self.api.list_crons_all(function_id=function_id):
            if cron.name == trigger.name:
                created_trigger = cron
        if not created_trigger:
            created_trigger = self.api.create_cron(
                function_id=function_id,
                schedule=trigger.schedule,
                name=trigger.name,
                args=trigger.args,
            )
        else:
            created_trigger = self.api.update_cron(
                cron_id=created_trigger.id,
                schedule=trigger.schedule,
                args=trigger.args,
            )
        return self.api.wait_for_cron(cron_id=created_trigger.id)

    def _create_deployment_zip(self) -> int:
        """Create a ZIP archive containing the entire project."""
        self.logger.default("Creating a deployment archive...")
        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)

        if os.path.exists(DEPLOYMENT_ZIP):
            os.remove(DEPLOYMENT_ZIP)

        create_zip_file(DEPLOYMENT_ZIP, "./")
        return os.path.getsize(DEPLOYMENT_ZIP)

    def _upload_deployment_zip(self, upload_url: str, zip_size: int):
        """Upload function zip to S3 presigned URL."""
        with open(DEPLOYMENT_ZIP, mode="rb") as file:
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

    def _remove_missing_functions(self, namespace_id: str):
        """Deletes functions no longer present in the code."""
        function_names = [func.name for func in self.app_instance.functions]
        for function in self.api.list_functions_all(namespace_id=namespace_id):
            if function.name not in function_names:
                self.logger.info(f"Deleting function {function.name}...")
                self.api.delete_function(function_id=function.id)

    def _remove_missing_triggers(self, namespace_id: str, deployed_triggers: set[str]):
        """Deletes triggers no longer present in the code."""
        for function in self.api.list_functions_all(namespace_id=namespace_id):
            unmanaged = filter(
                lambda c: c.id not in deployed_triggers,
                self.api.list_crons_all(function_id=function.id),
            )
            for cron in unmanaged:
                self.logger.info(f"Deleting Cron {cron.name}...")
                self.api.delete_cron(cron_id=cron.id)

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
        secrets = [
            sdk.Secret(key, value)
            for key, value in (self.app_instance.secret or {}).items()
        ]
        if not namespace:
            self.logger.default(
                f"Creating a new namespace {namespace_name} in {project_id}..."
            )
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
        namespace = self.api.wait_for_namespace(namespace_id=namespace.id)
        if namespace.status != sdk.NamespaceStatus.READY:
            raise ValueError(
                f"Namespace {namespace.name} is not ready: {namespace.error_message}"
            )
        return namespace.id

    def deploy(self) -> None:
        namespace_id = self._get_or_create_namespace()
        # Create a zip containing the user's project
        file_size = self._create_deployment_zip()

        deploy_inputs = [
            (function, namespace_id, file_size)
            for function in self.app_instance.functions
        ]
        triggers_to_deploy = {
            function.name: function.triggers
            for function in self.app_instance.functions
            if function.triggers
        }
        function_ids: dict[str, str] = {}

        n_proc = min(len(self.app_instance.functions), 3 * (os.cpu_count() or 1))
        with multiprocessing.Pool(processes=n_proc) as pool:
            for function in pool.starmap(self._deploy_function, deploy_inputs):
                if function.status is sdk.FunctionStatus.ERROR:
                    raise ValueError(
                        f"Function {function.name} is in error state: "
                        + (function.error_message or "")
                    )
                self.logger.success(
                    f"Function {function.name} deployed to: "
                    + f"https://{function.domain_name}"
                )
                function_ids[function.name] = function.id

            if triggers_to_deploy:
                self.logger.default("Deploying triggers...")

            triggers_to_deploy = [
                (function_ids[k], t)
                for k, triggers in triggers_to_deploy.items()
                for t in triggers
            ]

            deployed_triggers: set[str] = set()
            for trigger in pool.starmap(self._deploy_trigger, triggers_to_deploy):
                if trigger.status is sdk.CronStatus.ERROR:
                    raise ValueError(f"Trigger {trigger.name} is in error state")
                deployed_triggers.add(trigger.id)

        if self.single_source:
            # Remove functions no longer present in the code
            self._remove_missing_functions(namespace_id)
            # Remove triggers
            self._remove_missing_triggers(namespace_id, deployed_triggers)

        self.logger.success("Done! Functions have been successfully deployed!")
