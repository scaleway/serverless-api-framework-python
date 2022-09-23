from typing import Any, List

import logging
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


class TerraformGenerator(Generator):
    """
    Terraform Generator

    This class is responsible for generating Terraform Configuration
    """

    def __init__(self, instance: Serverless, deps_manager: DependenciesManager):
        self.instance = instance
        self.deps_manager = deps_manager

    def list_files(self, source):
        zip_files = []

        for path, _subdirs, files in os.walk(source):
            for name in files:
                zip_files.append(os.path.join(path, name))

        return zip_files

    def create_zip_file(self, zip_path, source):
        files = self.list_files(source)

        with ZipFile(zip_path, "w", strict_timestamps=False) as zip:
            for file in files:
                # Allow for safely running the generator multiple times
                if os.path.realpath(file) != os.path.realpath(zip_path):
                    zip.write(file)

    def _get_fn_args(self, fn: Function):
        supported_args = {  # List of supported args in terraform function configuration
            "min_scale": None,
            "max_scale": None,
            "memory_limit": None,
            "timeout": None,
            "description": None,
            "privacy": None,
            "env": "environment_variables",
        }
        config = {}
        for k, v in fn.args.items():
            if k in supported_args:
                config[supported_args[k] or k] = v
            else:
                # TODO: change this for custom logger
                logging.warning(
                    "found unsupported argument %s for %s"
                    % (k, self.__class__.__name__)
                )
        return config

    @singledispatchmethod
    def _res_from_event(self, event, i: int, fn: Function) -> dict[str, Any]:
        raise ValueError("received unsupported event %s", event)

    @_res_from_event.register
    def _(self, event: CronSchedule, i: int, fn: Function) -> dict[str, Any]:
        return {
            {
                f"{fn.name}_cron_{i+1}": {  # Functions may have multiple CRON triggers
                    "function_id": f"{TF_FUNCTION_RESOURCE}.{fn.name}.id",
                    "schedule": event.expression,
                    "args": event.inputs,
                }
            }
        }

    def _res_from_fn(
        self, fn: Function, python_version: str, zip_hash: str
    ) -> dict[str, Any]:
        args = self._get_fn_args(fn)
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

        self.create_zip_file(f"{path}/functions.zip", "./")
        with open(f"{path}/functions.zip", "rb") as f:
            zip_bytes = f.read()
            zip_hash = hashlib.sha256(zip_bytes).hexdigest()

        config["resource"][TF_NAMESPACE_RESOURCE] = {
            self.instance.service_name: {
                "name": f"{self.instance.service_name}-function-namespace",
                "description": f"{self.instance.service_name} function namespace",
            }
        }

        if self.instance.env is not None:
            config["resource"][TF_NAMESPACE_RESOURCE][self.instance.service_name][
                "environment_variables"
            ] = self.instance.env

        config["resource"][TF_FUNCTION_RESOURCE] = {}

        for fn in self.instance.functions:  # Iterate over the functions
            config["resource"][TF_FUNCTION_RESOURCE] |= self._res_from_fn(
                fn, version, zip_hash
            )
            for i, event in enumerate(fn.events):
                config["resource"][
                    TF_EVENTS_RESOURCES[event.kind]
                ] |= self._res_from_event(event, i, fn)

        functions = [
            fn.name for fn in self.instance.functions
        ]  # create a list containing the functions name

        config["resource"][TF_FUNCTION_RESOURCE] = {
            key: val
            for key, val in config["resource"][TF_FUNCTION_RESOURCE].items()
            if key in functions
        }  # remove not present functions from configuration file

        with open(config_path, "w") as file:
            json.dump(config, file, indent=2)
