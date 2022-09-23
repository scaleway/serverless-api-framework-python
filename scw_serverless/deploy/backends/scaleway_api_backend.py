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
from scw_serverless.utils import create_zip_file


class ScalewayApiBackend(ServerlessBackend):
    def __init__(self, app_instance: Serverless, single_source: bool):
        super().__init__(app_instance)
        self.single_source = single_source

    def deploy(self, deploy_config: DeployConfig):
        # Init the API Client
        api = Api(region=deploy_config.region, secret_key=deploy_config.secret_key)

        namespace = None

        self.logger.default(
            f"Looking for an existing namespace {self.app_instance.service_name} in {api.region}..."
        )
        # Search in the user's namespace if one is matching the same name and region
        for ns in api.list_namespaces(deploy_config.project_id):
            if ns["name"] == self.app_instance.service_name:
                namespace = ns["id"]

        new_namespace = False

        if namespace is None:
            self.logger.default(
                f"Creating a new namespace {self.app_instance.service_name} in {api.region}..."
            )
            # Create a new namespace
            ns = api.create_namespace(
                self.app_instance.service_name,
                deploy_config.project_id,
                self.app_instance.env,
                None,  # Description
                self.app_instance.secret,
            )

            if ns is None:
                raise RuntimeError("Unable to create a new namespace")

            namespace = ns["id"]
            new_namespace = True

            # Wait for the namespace to exit pending status
            namespace_data = api.get_namespace(namespace)
            while namespace_data["status"] == "pending":
                time.sleep(15)
                namespace_data = api.get_namespace(namespace)

        # Get the python version from the current env
        version = f"{sys.version_info.major}{sys.version_info.minor}"
        self.logger.info(f"Using python{version}")

        # Create a ZIP archive containing the entire project
        self.logger.default("Creating a deployment archive...")
        if not os.path.exists("./.scw"):
            os.mkdir("./.scw")

        if os.path.exists("./.scw/deployment.zip"):
            os.remove("./.scw/deployment.zip")

        create_zip_file("./.scw/deployment.zip", "./")
        file_size = os.path.getsize("./.scw/deployment.zip")

        # For each function
        for func in self.app_instance.functions:
            self.logger.default(
                f"Looking for an existing function {func['function_name']}..."
            )
            target_function = None
            domain = None

            # Looking if a function is already existing
            for fn in api.list_functions(namespace_id=namespace):
                if fn["name"] == func["function_name"]:
                    target_function = fn["id"]
                    domain = fn["domain_name"]

            fn_args = func["args"]

            if target_function is None:
                self.logger.default(
                    f"Creating a new function {func['function_name']}..."
                )

                # Creating a new function with the provided args
                fn = api.create_function(
                    namespace_id=namespace,
                    name=func["function_name"],
                    runtime=f"python{version}",
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
                api.update_function(
                    function_id=target_function,
                    runtime=f"python{version}",
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

            # Get an object storage pre-signed url
            upload_url = api.upload_function(
                function_id=target_function, content_length=file_size
            )

            if not upload_url:
                raise RuntimeError(
                    "Unable to retrieve upload url... Verify that your function is less that 8.388608e+08 MB"
                )

            self.logger.default("Uploading function...")
            with open(".scw/deployment.zip", "rb") as file:
                # Upload function zip to S3 presigned URL
                req = requests.put(
                    upload_url,
                    data=file,
                    headers={
                        "Content-Type": "application/octet-stream",
                        "Content-Length": str(file_size),
                    },
                )

                if req.status_code != 200:
                    raise RuntimeError("Unable to upload function code... Aborting...")

            self.logger.default("Deploying function...")
            # deploy the newly uploaded function
            if not api.deploy_function(target_function):
                self.logger.error(
                    f"Unable to deploy function {func['function_name']}..."
                )
            else:

                # Wait for the function to become ready or in error state.
                status = api.get_function(target_function)["status"]
                while status not in [
                    "ready",
                    "error",
                ]:
                    time.sleep(30)
                    status = api.get_function(target_function)["status"]

                if status == "error":
                    self.logger.error(
                        f"Unable to deploy {func['function_name']}. Status is in error state."
                    )
                else:
                    self.logger.success(
                        f"Function {func['function_name']} has been deployed to https://{domain}"
                    )

        if not new_namespace:
            click.echo("Updating namespace configuration...")
            # Update the namespace
            api.update_namespace(
                namespace,
                self.app_instance.env,
                None,  # Description
                self.app_instance.secret,
            )

        if self.single_source:
            # Delete functions no longer present in the code...
            # create a list containing the functions name
            functions = list(
                map(lambda x: x["function_name"], self.app_instance.functions)
            )

            for func in api.list_functions(namespace):
                if func["name"] not in functions:
                    self.logger.warning(f"Deleting function {func['name']}...")
                    api.delete_function(func["id"])

        self.logger.success(f"Done! Functions have been successfully deployed!")
