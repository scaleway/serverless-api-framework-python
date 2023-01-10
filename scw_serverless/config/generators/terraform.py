import hashlib
import json
import os
import re
from dataclasses import dataclass
from functools import singledispatch
from typing import Any, Optional, Tuple

from scw_serverless.app import Serverless
from scw_serverless.config.function import Function
from scw_serverless.config.generators.generator import Generator
from scw_serverless.config.utils import _SerializableDataClass
from scw_serverless.dependencies_manager import DependenciesManager
from scw_serverless.triggers import CronTrigger
from scw_serverless.utils.files import create_zip_file

TERRAFORM_OUTPUT_FILE = "terraform.tf.json"
TF_FUNCTION_RESOURCE = "scaleway_function"
TF_NAMESPACE_RESOURCE = "scaleway_function_namespace"
TF_CRON_RESOURCE = "scaleway_function_cron"

EventConfig = Tuple[str, dict[str, Any]]


@singledispatch
def _get_event_config(trigger) -> EventConfig:
    raise ValueError(f"Received unsupported event: {trigger}")


@_get_event_config.register
def _(cron: CronTrigger) -> EventConfig:
    config = {"schedule": cron.schedule}
    if cron.args:
        config |= {"args": json.dumps(cron.args)}
    return TF_CRON_RESOURCE, config


# pylint: disable=too-many-instance-attributes
@dataclass
class _TerraformFunctionResource(_SerializableDataClass):
    namespace_id: str
    name: str
    handler: str
    runtime: str
    zip_file: str
    zip_hash: str
    min_scale: Optional[int]
    max_scale: Optional[int]
    memory_limit: Optional[int]
    timeout: Optional[int]
    description: Optional[str]
    privacy: Optional[str]
    environment_variables: Optional[dict[str, str]]
    secret_environment_variables: Optional[dict[str, str]]

    @property
    def resource_name(self) -> str:
        """Gets the resource name in snake case"""
        return self.name.replace("-", "_")

    @staticmethod
    def parse_timeout(timeout: str) -> int:
        """Parses timeout to a duration in seconds."""
        if match := re.match(r"(\d*\.\d+|\d+)s", timeout):
            return int(match.group(1))
        raise ValueError(f"Could not parse timeout: {timeout}")

    @staticmethod
    def from_function(
        function: Function, namespace_id: str, zip_file: str, zip_hash: str
    ):
        """Creates a scaleway_function resource from a Function."""
        timeout = None
        if function.timeout:
            timeout = _TerraformFunctionResource.parse_timeout(function.timeout)
        # Required by Terraform
        privacy = function.privacy if function.privacy else "public"
        return _TerraformFunctionResource(
            namespace_id=namespace_id,
            name=function.name,
            handler=function.handler,
            runtime=function.runtime,
            zip_file=zip_file,
            zip_hash=zip_hash,
            min_scale=function.min_scale,
            max_scale=function.max_scale,
            memory_limit=function.memory_limit,
            timeout=timeout,
            description=function.description,
            privacy=privacy,
            environment_variables=function.environment_variables,
            secret_environment_variables=function.secrets_asdict(),
        )


@dataclass
class _TerraformNamespaceResource(_SerializableDataClass):
    name: str
    description: Optional[str]
    environment_variables: Optional[dict[str, str]]
    secret_environment_variables: Optional[dict[str, str]]

    @property
    def resource_name(self) -> str:
        """Gets the resource name in snake case."""
        return self.name.replace("-", "_")

    @staticmethod
    def from_serverless(serverless: Serverless):
        """Creates a scaleway_function_namespace resource from Serverless."""
        return _TerraformNamespaceResource(
            name=serverless.service_name,
            description=None,
            environment_variables=serverless.env,
            secret_environment_variables=serverless.secret,
        )


class TerraformGenerator(Generator):
    """Generates the Terraform configuration to deploy the functions.

    .. seealso:: https://registry.terraform.io/providers/scaleway/scaleway/latest/docs/resources/function
    """

    def __init__(self, instance: Serverless, deps_manager: DependenciesManager):
        self.instance = instance
        self.deps_manager = deps_manager
        self.zip_path = None
        self.zip_hash = None

    def _add_function_config(
        self, config: dict[str, Any], function: Function, namespace_id: str
    ):
        if not self.zip_path or not self.zip_hash:
            raise ValueError("Functions can only be added after the zip is created")
        resource = _TerraformFunctionResource.from_function(
            function, namespace_id, self.zip_path, self.zip_hash
        )
        config["resource"][TF_FUNCTION_RESOURCE] |= {
            resource.resource_name: resource.asdict()
        }
        function_id = f"{TF_FUNCTION_RESOURCE}.{resource.resource_name}.id"

        for i, trigger in enumerate(function.triggers or []):
            (tf_resource, event_config) = _get_event_config(trigger)
            event_config["function_id"] = function_id
            if tf_resource not in config["resource"]:
                config["resource"][tf_resource] = {}
            config["resource"][tf_resource] |= {
                f"{resource.resource_name}_trigger_{i}": event_config
            }

    def write(self, path: str) -> None:
        """Generates a terraform.tf.json file to path."""

        self.deps_manager.generate_package_folder()

        self.zip_path = os.path.join(path, "functions.zip")
        create_zip_file(self.zip_path, "./")

        with open(self.zip_path, mode="rb") as archive:
            zip_bytes = archive.read()
            self.zip_hash = hashlib.sha256(zip_bytes).hexdigest()

        config_path = os.path.join(path, TERRAFORM_OUTPUT_FILE)
        config_to_read = config_path

        if not os.path.exists(config_path):
            config_to_read = os.path.join(
                os.path.dirname(__file__), "..", "templates", TERRAFORM_OUTPUT_FILE
            )

        with open(config_to_read, mode="rt", encoding="utf-8") as file:
            config = json.load(file)

            namespace_resource = _TerraformNamespaceResource.from_serverless(
                self.instance
            )
            if TF_NAMESPACE_RESOURCE not in config["resource"]:
                config["resource"][TF_NAMESPACE_RESOURCE] = {}
            config["resource"][TF_NAMESPACE_RESOURCE] |= {
                namespace_resource.resource_name: namespace_resource.asdict()
            }
            namespace_id = (
                f"{TF_NAMESPACE_RESOURCE}.{namespace_resource.resource_name}.id"
            )

            config["resource"][TF_FUNCTION_RESOURCE] = {}
            for function in self.instance.functions:
                self._add_function_config(config, function, namespace_id)

            with open(config_path, mode="wt", encoding="utf-8") as config_file:
                json.dump(config, config_file, indent=2)
