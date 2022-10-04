from asyncio.log import logger
from typing import Any

import re
import json
import hashlib
import json
import os
import sys
from functools import singledispatchmethod
from zipfile import ZipFile

from ...events.schedule import CronSchedule
from .generator import Generator
from ..function import Function
from ...app import Serverless
from ...dependencies_manager import DependenciesManager

TERRAFORM_OUTPUT_FILE = "terraform.tf.json"
TF_FUNCTION_RESOURCE = "scaleway_function"
TF_NAMESPACE_RESOURCE = "scaleway_function_namespace"
TF_EVENTS_RESOURCES = {"schedule": "scaleway_function_cron"}


def _list_files(source):
    zip_files = []

    for path, _subdirs, files in os.walk(source):
        for name in files:
            zip_files.append(os.path.join(path, name))

    return zip_files


def _create_zip_file(zip_path, source):
    files = _list_files(source)

    with ZipFile(zip_path, "w", strict_timestamps=False) as zip:
        for file in files:
            # Allow for safely running the generator multiple times
            if os.path.realpath(file) != os.path.realpath(zip_path):
                zip.write(file)


class TerraformGenerator(Generator):
    """
    Terraform Generator

    This class is responsible for generating Terraform Configuration
    """

    def __init__(self, instance: Serverless, deps_manager: DependenciesManager):
        self.instance = instance
        self.deps_manager = deps_manager

    @staticmethod
    def get_allowed_args() -> dict[str, str]:
        # List of supported args in terraform function configuration
        allowed = [
            "min_scale",
            "max_scale",
            "memory_limit",
            "timeout",
            "description",
            "privacy",
        ]
        return {k: k for k in allowed} | {"env": "environment_variables"}

    @singledispatchmethod
    def _get_event_resource(self, event, i: int, fn: Function) -> dict[str, Any]:
        raise ValueError("received unsupported event %s", event)

    @_get_event_resource.register
    def _(self, event: CronSchedule, i: int, fn: Function) -> dict[str, Any]:
        return {
            f"{fn.name}-cron-{i+1}": {  # Functions may have multiple CRON triggers
                "function_id": f"{TF_FUNCTION_RESOURCE}.{fn.name}.id",
                "schedule": event.expression,
                "args": json.dumps(event.inputs),
            }
        }

    def _get_function_resource(
        self, fn: Function, python_version: str, zip_hash: str
    ) -> dict[str, Any]:
        args = self.get_fn_args(fn)
        if "timeout" in args:
            if match := re.match(r"(\d*\.\d+|\d+)s", args["timeout"]):
                args["timeout"] = float(match.group(1))
            else:
                logger.warning("could not parse timeout %s" % args["timeout"])
                del args["timeout"]
        return {
            fn.name: {
                "namespace_id": (
                    "${%s.%s.id}" % (TF_NAMESPACE_RESOURCE, self.instance.service_name)
                ),
                "runtime": f"python{python_version}",
                "handler": fn.handler_path,
                "name": fn.name,
                "zip_file": "functions.zip",
                "zip_hash": zip_hash,
                "deploy": True,
            }
            | args
        }

    def _get_namespace_resource(self) -> dict[str, Any]:
        namespace = self.instance.service_name
        inner = {
            "name": f"{namespace}-function-namespace",
            "description": f"{namespace} function namespace",
        }
        if self.instance.env is not None:
            inner["environment_variables"] = self.instance.env
        return {namespace: inner}

    def write(self, path: str):
        version = f"{sys.version_info.major}{sys.version_info.minor}"  # Get the python version from the current env
        config_path = os.path.join(path, TERRAFORM_OUTPUT_FILE)

        config_to_read = config_path

        if not os.path.exists(config_path):
            config_to_read = os.path.join(
                os.path.dirname(__file__), "..", "templates", TERRAFORM_OUTPUT_FILE
            )

        with open(config_to_read, "r") as file:
            config = json.load(file)

        self.deps_manager.generate_package_folder()

        _create_zip_file(f"{path}/functions.zip", "./")
        with open(f"{path}/functions.zip", "rb") as f:
            zip_bytes = f.read()
            zip_hash = hashlib.sha256(zip_bytes).hexdigest()

        config["resource"][TF_NAMESPACE_RESOURCE] = self._get_namespace_resource()

        config["resource"][TF_FUNCTION_RESOURCE] = {}
        for fn in self.instance.functions:  # Iterate over the functions
            config["resource"][TF_FUNCTION_RESOURCE] |= self._get_function_resource(
                fn, version, zip_hash
            )
            for i, event in enumerate(fn.events):
                if TF_EVENTS_RESOURCES[event.kind] not in config["resource"]:
                    config["resource"][TF_EVENTS_RESOURCES[event.kind]] = {}
                config["resource"][
                    TF_EVENTS_RESOURCES[event.kind]
                ] |= self._get_event_resource(event, i, fn)

        with open(config_path, "w") as file:
            json.dump(config, file, indent=2)
