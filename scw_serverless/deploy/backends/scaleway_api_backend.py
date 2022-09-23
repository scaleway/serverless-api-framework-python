import os
import sys
import time

import click
import requests

from scw_serverless.api import Api
from scw_serverless.app import Serverless
from scw_serverless.deploy.backends.serverless_backend import (
    ServerlessBackend,
    DeployConfig,
)
from scw_serverless.utils.files import create_zip_file

TEMP_DIR = "./.scw"
DEPLOYMENT_ZIP = f"{TEMP_DIR}/deployment.zip"


class ScalewayApiBackend(ServerlessBackend):
    def __init__(
        self, app_instance: Serverless, deploy_config: DeployConfig, single_source: bool
    ):
        super().__init__(app_instance, deploy_config)
        self.single_source = single_source

        # Init the self.api Client
        self.api = Api(
            region=self.deploy_config.region, secret_key=self.deploy_config.secret_key
        )

    def _get_or_create_function(self, func: dict, namespace: str):
        self.logger.default(
            f"Looking for an existing function {func['function_name']}..."
        )
        target_function = None
        domain = None

        # Looking if a function is already existing
        for fn in self.api.list_functions(namespace_id=namespace):
            if fn["name"] == func["function_name"]:
                target_function = fn["id"]
                domain = fn["domain_name"]

        fn_args = func["args"]

        if target_function is None:
            self.logger.default(f"Creating a new function {func['function_name']}...")

            # Creating a new function with the provided args
            fn = self.api.create_function(
                namespace_id=namespace,
                name=func["function_name"],
                runtime=f"python{self._get_python_version()}",
                handler=func["handler"],
                privacy=fn_args.get("privacy", "unknown_privacy"),
                env=fn_args.get("env"),
                min_scale=fn_args.get("min_scale"),
                max_scale=fn_args.get("max_scale"),
                memory_limit=fn_args.get("memory_limit"),
                timeout=fn_args.get("timeout"),
                description=fn_args.get("description"),
                secrets=fn_args.get("secret"),
            )

            if fn is None:
                raise RuntimeError("Unable to create a new function")

            target_function = fn["id"]
            domain = fn["domain_name"]
        else:
            # Updating the function with the provided args
            self.api.update_function(
                function_id=target_function,
                runtime=f"python{self._get_python_version()}",
                handler=func["handler"],
                privacy=fn_args.get("privacy", "unknown_privacy"),
                env=fn_args.get("env"),
                min_scale=fn_args.get("min_scale"),
                max_scale=fn_args.get("max_scale"),
                memory_limit=fn_args.get("memory_limit"),
                timeout=fn_args.get("timeout"),
                description=fn_args.get("description"),
                secrets=fn_args.get("secret"),
            )

        return target_function, domain

    def _deploy_function(self, func: dict, namespace: str, zip_size: int):
        target_function, domain = self._get_or_create_function(
            func=func, namespace=namespace
        )

        # Get an object storage pre-signed url
        upload_url = self.api.upload_function(
            function_id=target_function, content_length=zip_size
        )

        if not upload_url:
            raise RuntimeError(
                "Unable to retrieve upload url... Verify that your function is less that 100 MB"
            )

        self.logger.default("Uploading function...")
        with open(DEPLOYMENT_ZIP, "rb") as file:
            # Upload function zip to S3 presigned URL
            req = requests.put(
                upload_url,
                data=file,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(zip_size),
                },
            )

            if req.status_code != 200:
                raise RuntimeError("Unable to upload function code... Aborting...")

        self.logger.default("Deploying function...")
        # deploy the newly uploaded function
        if not self.api.deploy_function(target_function):
            self.logger.error(f"Unable to deploy function {func['function_name']}...")
        else:

            # Wait for the function to become ready or in error state.
            status = self.api.get_function(target_function)["status"]
            while status not in [
                "ready",
                "error",
            ]:
                time.sleep(30)
                status = self.api.get_function(target_function)["status"]

            if status == "error":
                self.logger.error(
                    f"Unable to deploy {func['function_name']}. Status is in error state."
                )
            else:
                self.logger.success(
                    f"Function {func['function_name']} has been deployed to https://{domain}"
                )

    def _get_python_version(self):
        # Get the python version from the current env
        return f"{sys.version_info.major}{sys.version_info.minor}"

    def _create_deployment_zip(self):
        # Create a ZIP archive containing the entire project
        self.logger.default("Creating a deployment archive...")
        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)

        if os.path.exists(DEPLOYMENT_ZIP):
            os.remove(DEPLOYMENT_ZIP)

        create_zip_file(DEPLOYMENT_ZIP, "./")
        return os.path.getsize(DEPLOYMENT_ZIP)

    def _remove_missing_functions(self, namespace: str):
        # Delete functions no longer present in the code...

        # create a list containing the functions name
        functions = list(map(lambda x: x["function_name"], self.app_instance.functions))

        for func in self.api.list_functions(namespace):
            if func["name"] not in functions:
                self.logger.warning(f"Deleting function {func['name']}...")
                self.api.delete_function(func["id"])

    def _get_or_create_namespace(self):
        namespace = None

        self.logger.default(
            f"Looking for an existing namespace {self.app_instance.service_name} in {self.api.region}..."
        )
        # Search in the user's namespace if one is matching the same name and region
        for ns in self.api.list_namespaces(self.deploy_config.project_id):
            if ns["name"] == self.app_instance.service_name:
                namespace = ns["id"]

        new_namespace = False

        if namespace is None:
            self.logger.default(
                f"Creating a new namespace {self.app_instance.service_name} in {self.api.region}..."
            )
            # Create a new namespace
            ns = self.api.create_namespace(
                name=self.app_instance.service_name,
                project_id=self.deploy_config.project_id,
                env=self.app_instance.env,
                secrets=self.app_instance.secret,
            )

            if ns is None:
                raise RuntimeError("Unable to create a new namespace")

            namespace = ns["id"]
            new_namespace = True

            # Wait for the namespace to exit pending status
            namespace_data = self.api.get_namespace(namespace)
            while namespace_data["status"] == "pending":
                time.sleep(15)
                namespace_data = self.api.get_namespace(namespace)

        return namespace, new_namespace

    def deploy(self):
        namespace, new_namespace = self._get_or_create_namespace()

        self.logger.info(f"Using python{self._get_python_version()}")

        # Create a zip containing the user's project
        file_size = self._create_deployment_zip()

        # For each function
        for func in self.app_instance.functions:
            # Deploy the function
            self._deploy_function(func=func, namespace=namespace, zip_size=file_size)

        if not new_namespace:
            click.echo("Updating namespace configuration...")
            # Update the namespace
            self.api.update_namespace(
                namespace_id=namespace,
                env=self.app_instance.env,
                secrets=self.app_instance.secret,
            )

        if self.single_source:
            # Remove functions no longer present in the code
            self._remove_missing_functions(namespace=namespace)

        self.logger.success(f"Done! Functions have been successfully deployed!")
