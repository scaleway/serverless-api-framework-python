import logging
import multiprocessing
import os

import click
import requests
import scaleway.function.v1beta1 as sdk
from scaleway import Client, ScalewayException

from scw_serverless.app import Serverless
from scw_serverless.config.function import Function
from scw_serverless.config.triggers import CronTrigger
from scw_serverless.deployment.api_wrapper import FunctionAPIWrapper
from scw_serverless.utils.files import create_zip_file

TEMP_DIR = "./.scw"
DEPLOYMENT_ZIP = f"{TEMP_DIR}/deployment.zip"
UPLOAD_TIMEOUT = 600  # In seconds


class DeploymentManager:
    """Uses the API to deploy functions."""

    def __init__(
        self,
        app_instance: Serverless,
        sdk_client: Client,
        single_source: bool,
        runtime: str,
    ):
        self.api = FunctionAPIWrapper(api=sdk.FunctionV1Beta1API(sdk_client))
        self.app_instance = app_instance
        self.sdk_client = sdk_client
        # Behavior configuration
        self.single_source = single_source
        self.runtime = sdk.FunctionRuntime(runtime)

    def _get_or_create_function(self, function: Function, namespace_id: str) -> str:
        logging.info("Looking for an existing function %s...", function.name)
        # Checking if a function already exists
        deployed_function = self.api.find_deployed_function(
            namespace_id=namespace_id, function=function
        )
        if not deployed_function:
            logging.info("Creating a new function %s...", function.name)
            # Creating a new function with the provided args
            deployed_function = self.api.create_function(
                namespace_id=namespace_id, function=function, runtime=self.runtime
            )
        else:
            # Updating the function with the provided args
            deployed_function = self.api.update_function(
                function_id=deployed_function.id,
                function=function,
                runtime=self.runtime,
            )
        return deployed_function.id

    def _deploy_function(
        self, function: Function, namespace_id: str, zip_size: int
    ) -> sdk.Function:
        function_id = self._get_or_create_function(function, namespace_id)

        # Get an object storage pre-signed url
        try:
            upload_url = self.api.get_upload_url(
                function_id=function_id, zip_size=zip_size
            )
        except ScalewayException as e:
            logging.error(
                "Unable to retrieve upload url... "
                "Verify that your function is less that 100 MB"
            )
            raise e

        logging.info("Uploading function %s...", function.name)
        self._upload_deployment_zip(upload_url, zip_size)

        logging.info("Deploying function %s...", function.name)
        # Deploy the newly uploaded function
        return self.api.deploy_function(function_id=function_id)

    def _deploy_cron_trigger(self, function_id: str, trigger: CronTrigger) -> sdk.Cron:
        # Checking if a trigger already exists
        deployed_trigger = self.api.find_deployed_cron_trigger(
            function_id=function_id, trigger=trigger
        )
        if not deployed_trigger:
            deployed_trigger = self.api.create_cron_trigger(
                function_id=function_id, trigger=trigger
            )
        else:
            deployed_trigger = self.api.update_cron_trigger(
                function_id=function_id, trigger=trigger
            )
        return deployed_trigger

    def _create_deployment_zip(self) -> int:
        """Create a ZIP archive containing the entire project."""
        logging.info("Creating a deployment archive...")
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

    def _get_or_create_namespace(self) -> str:
        namespace_name = self.app_instance.service_name
        project_id = self.sdk_client.default_project_id
        logging.debug(
            "Looking for an existing namespace %s in project %s...",
            namespace_name,
            project_id,
        )
        deployed_namespace = self.api.find_deployed_namespace(
            app_instance=self.app_instance
        )
        if not deployed_namespace:
            logging.info(
                "Creating a new namespace %s in %s...", namespace_name, project_id
            )
            deployed_namespace = self.api.create_namespace(
                app_instance=self.app_instance
            )
        else:
            logging.debug("Updating namespace %s configuration...", namespace_name)
            deployed_namespace = self.api.update_namespace(
                namespace_id=deployed_namespace.id, app_instance=self.app_instance
            )
        if deployed_namespace.status != sdk.NamespaceStatus.READY:
            raise ValueError(
                f"Namespace {deployed_namespace.name} is not ready: "
                + (deployed_namespace.error_message or "")
            )
        return deployed_namespace.id

    def deploy(self) -> None:
        """Deploy all configured functions using the Scaleway API."""
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
                click.secho(
                    f"Function {function.name} deployed to: "
                    + f"https://{function.domain_name}",
                    fg="green",
                )
                function_ids[function.name] = function.id

            if triggers_to_deploy:
                logging.info("Deploying triggers...")

            triggers_to_deploy = [
                (function_ids[k], t)
                for k, triggers in triggers_to_deploy.items()
                for t in triggers
            ]

            deployed_triggers: set[str] = set()
            for trigger in pool.starmap(self._deploy_cron_trigger, triggers_to_deploy):
                if trigger.status is sdk.CronStatus.ERROR:
                    raise ValueError(f"Trigger {trigger.name} is in error state")
                deployed_triggers.add(trigger.id)

        click.secho("Done! Functions have been successfully deployed!", fg="green")

        if self.single_source:
            # Remove functions no longer present in the code
            self.api.delete_all_functions_from_ns_except(
                namespace_id=namespace_id, function_ids=list(function_ids.values())
            )
            # Remove triggers
            self.api.delete_all_crons_from_ns_except(
                namespace_id=namespace_id, cron_ids=list(deployed_triggers)
            )
