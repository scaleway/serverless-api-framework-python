from typing import Any

import os
import sys
from functools import singledispatchmethod

import yaml

from ..function import Function
from ...events.schedule import CronSchedule
from ...utils import to_camel_case
from .generator import Generator
from ...app import Serverless


class ServerlessFrameworkGenerator(Generator):
    """
    Serverless Framework Generator

    This class is responsible for generating a serverless.yml config file
    """

    def __init__(self, instance: Serverless):
        self.instance = instance

    @staticmethod
    def get_allowed_args() -> dict[str, str]:
        # List of allowed args in serverless framework function configuration
        allowed = [
            "env",
            "secret",
            "min_scale",
            "max_scale",
            "memory_limit",
            "timeout",
            "privacy",
            "description",
        ]
        return {k: to_camel_case(k) for k in allowed} | {
            "custom_domains": "custom_domains"
        }

    @singledispatchmethod
    def _get_event_config(self, event) -> dict[str, Any]:
        raise ValueError("received unsupported event %s", event)

    @_get_event_config.register
    def _(self, event: CronSchedule) -> dict[str, Any]:
        return {"schedule": {"rate": event.expression, "input": event.inputs}}

    def _get_function_config(self, fn: Function) -> dict[str, Any]:
        config = self.get_fn_args(fn)
        if fn.events:
            config["events"] = [self._get_event_config(event) for event in fn.events]
        config["handler"] = fn.handler_path
        return config

    def write(self, path):
        version = f"{sys.version_info.major}{sys.version_info.minor}"  # Get the python version from the current env
        config_path = os.path.join(path, "serverless.yml")

        config_to_read = config_path

        # If there is no serverless.yml file existing. Use the one in the templates folder
        if not os.path.exists(config_path):
            config_to_read = os.path.join(
                os.path.dirname(__file__), "..", "templates", "serverless.yml"
            )

        # Open and read the configuration file
        with open(config_to_read, "r") as file:
            config = yaml.safe_load(file)

        config["service"] = self.instance.service_name  # Update the service name
        config["provider"]["runtime"] = f"python{version}"  # Update the runtime

        if self.instance.env is not None:
            config["provider"]["env"] = self.instance.env
        if self.instance.secret is not None:
            config["provider"]["secret"] = self.instance.secret

        config["functions"] = {fn.name: {} for fn in self.instance.functions}
        for fn in self.instance.functions:  # Iterate over the functions
            config["functions"][fn.name] = self._get_function_config(fn)

        with open(config_path, "w") as file:
            yaml.dump(config, file)  # Write serverless.yml
