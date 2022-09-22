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
from scw_serverless.logger import get_logger
from scw_serverless.utils import create_zip_file


class ScalewayApiBackend(ServerlessBackend):
    def __init__(self, app_instance: Serverless, single_source: bool):
        self.app_instance = app_instance
        self.single_source = single_source

    def deploy(self, deploy_config: DeployConfig):
        api = Api(
            region=deploy_config.region, secret_key=deploy_config.secret_key
        )  # Init the API Client

        namespace = None

        get_logger().default(
            f"Looking for an existing namespace {self.app_instance.service_name} in {api.region}..."
        )
        for ns in api.list_namespaces(
            deploy_config.project_id
        ):  # Search in the user's namespace if one is matching the same name and region
            if ns["name"] == self.app_instance.service_name:
                namespace = ns["id"]

        new_namespace = False

        if namespace is None:
            get_logger().default(
                f"Creating a new namespace {self.app_instance.service_name} in {api.region}..."
            )
            ns = api.create_namespace(  # Create a new namespace
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

        version = f"{sys.version_info.major}{sys.version_info.minor}"  # Get the python version from the current env
        get_logger().info(f"Using python{version}")

        # Create a ZIP archive containing the entire project
        get_logger().default("Creating a deployment archive...")
        if not os.path.exists("./.scw"):
            os.mkdir("./.scw")

        if os.path.exists("./.scw/deployment.zip"):
            os.remove("./.scw/deployment.zip")

        create_zip_file("./.scw/deployment.zip", "./")
        file_size = os.path.getsize("./.scw/deployment.zip")

        for func in self.app_instance.functions:  # For each function
            get_logger().default(
                f"Looking for an existing function {func['function_name']}..."
            )
            target_function = None
            domain = None

            for fn in api.list_functions(
                namespace_id=namespace
            ):  # Looking if a function is already existing
                if fn["name"] == func["function_name"]:
                    target_function = fn["id"]
                    domain = fn["domain_name"]

            if target_function is None:
                get_logger().default(
                    f"Creating a new function {func['function_name']}..."
                )

                fn = api.create_function(  # Creating a new function with the provided args
                    namespace_id=namespace,
                    name=func["function_name"],
                    runtime=f"python{version}",
                    handler=func["handler"],
                    privacy=func["args"]["privacy"]
                    if "privacy" in func["args"]
                    else "unknown_privacy",
                    env=func["args"]["env"] if "env" in func["args"] else None,
                    min_scale=func["args"]["min_scale"]
                    if "min_scale" in func["args"]
                    else None,
                    max_scale=func["args"]["max_scale"]
                    if "max_scale" in func["args"]
                    else None,
                    memory_limit=func["args"]["memory_limit"]
                    if "memory_limit" in func["args"]
                    else None,
                    timeout=func["args"]["timeout"]
                    if "timeout" in func["args"]
                    else None,
                    description=func["args"]["description"]
                    if "description" in func["args"]
                    else None,
                    secrets=func["args"]["secret"]
                    if "secret" in func["args"]
                    else None,
                )

                if fn is None:
                    raise RuntimeError("Unable to create a new function")

                target_function = fn["id"]
                domain = fn["domain_name"]
            else:
                api.update_function(  # Updating the function with the provided args
                    function_id=target_function,
                    runtime=f"python{version}",
                    handler=func["handler"],
                    privacy=func["args"]["privacy"]
                    if "privacy" in func["args"]
                    else "unknown_privacy",
                    env=func["args"]["env"] if "env" in func["args"] else None,
                    min_scale=func["args"]["min_scale"]
                    if "min_scale" in func["args"]
                    else None,
                    max_scale=func["args"]["max_scale"]
                    if "max_scale" in func["args"]
                    else None,
                    memory_limit=func["args"]["memory_limit"]
                    if "memory_limit" in func["args"]
                    else None,
                    timeout=func["args"]["timeout"]
                    if "timeout" in func["args"]
                    else None,
                    description=func["args"]["description"]
                    if "description" in func["args"]
                    else None,
                    secrets=func["args"]["secret"]
                    if "secret" in func["args"]
                    else None,
                )

            # Get an object storage pre-signed url
            upload_url = api.upload_function(
                function_id=target_function, content_length=file_size
            )

            if upload_url is None:
                raise RuntimeError(
                    "Unable to retrieve upload url... Verify that your function is less that 8.388608e+08 MB"
                )

            get_logger().default("Uploading function...")
            with open(".scw/deployment.zip", "rb") as file:
                req = requests.put(  # Upload function zip to S3 presigned URL
                    upload_url,
                    data=file,
                    headers={
                        "Content-Type": "application/octet-stream",
                        "Content-Length": str(file_size),
                    },
                )

                if req.status_code != 200:
                    raise RuntimeError("Unable to upload function code... Aborting...")

            get_logger().default("Deploying function...")
            if not api.deploy_function(
                target_function
            ):  # deploy the newly uploaded function
                get_logger().error(
                    f"Unable to deploy function {func['function_name']}..."
                )
            else:

                status = api.get_function(target_function)["status"]
                while status not in [
                    "ready",
                    "error",
                ]:  # Wait for the function to become ready or in error state.
                    time.sleep(30)
                    status = api.get_function(target_function)["status"]

                if status == "error":
                    get_logger().error(
                        f"Unable to deploy {func['function_name']}. Status is in error state."
                    )
                else:
                    get_logger().success(
                        f"Function {func['function_name']} has been deployed to https://{domain}"
                    )

        if not new_namespace:
            click.echo("Updating namespace configuration...")
            api.update_namespace(  # Update the namespace
                namespace,
                self.app_instance.env,
                None,  # Description
                self.app_instance.secret,
            )

        if self.single_source:
            # Delete functions no longer present in the code...
            functions = list(
                map(lambda x: x["function_name"], self.app_instance.functions)
            )  # create a list containing the functions name

            for func in api.list_functions(namespace):
                if func["name"] not in functions:
                    get_logger().warning(f"Deleting function {func['name']}...")
                    api.delete_function(func["id"])

        get_logger().success(f"Done! Functions have been successfully deployed!")
