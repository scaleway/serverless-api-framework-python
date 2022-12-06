import os
from dataclasses import dataclass
from functools import singledispatch
from typing import Any, Optional

import yaml

from scw_serverless.app import Serverless
from scw_serverless.config.function import Function
from scw_serverless.config.generators.generator import Generator
from scw_serverless.config.utils import _SerializableDataClass
from scw_serverless.triggers import CronTrigger

EventConfig = dict[str, Any]


@singledispatch
def _get_event_config(trigger) -> EventConfig:
    raise ValueError(f"Received unsupported event: {trigger}")


@_get_event_config.register
def _(cron: CronTrigger) -> EventConfig:
    config = {"schedule": {"rate": cron.schedule}}
    if cron.args:
        config["input"] = cron.args
    return config


# pylint: disable=too-many-instance-attributes
@dataclass
class _ServerlessFrameworkFunction(_SerializableDataClass):
    handler: str
    env: Optional[dict[str, str]]
    secret: Optional[dict[str, str]]
    # pylint: disable=invalid-name # used for serialization
    minScale: Optional[int]
    maxScale: Optional[int]
    memoryLimit: Optional[int]
    # pylint: enable=invalid-name
    timeout: Optional[str]
    privacy: Optional[str]
    description: Optional[str]
    custom_domains: Optional[list[str]]
    events: Optional[list[EventConfig]]

    @staticmethod
    def from_function(function: Function):
        """Creates a ServerlessFramework function config from a Function."""
        events = None
        if function.triggers:
            events = [_get_event_config(trigger) for trigger in function.triggers]
        return _ServerlessFrameworkFunction(
            handler=function.handler,
            env=function.environment_variables,
            secret=function.secrets_asdict(),
            minScale=function.min_scale,
            maxScale=function.max_scale,
            memoryLimit=function.memory_limit,
            timeout=function.timeout,
            privacy=str(function.privacy) if function.privacy else None,
            description=function.description,
            custom_domains=function.domains if function.domains else None,
            events=events,
        )


class ServerlessFrameworkGenerator(Generator):
    """Generates a serverless.yml config file.

    See also:
    https://github.com/scaleway/serverless-scaleway-functions
    """

    def __init__(self, instance: Serverless):
        self.instance = instance

    def write(self, path: str):
        """Generates a serverless.yml file to path."""

        config_path = os.path.join(path, "serverless.yml")
        config_to_read = config_path
        # If there is no serverless.yml file existing, use the template
        if not os.path.exists(config_path):
            config_to_read = os.path.join(
                os.path.dirname(__file__), "..", "templates", "serverless.yml"
            )

        # Open and read the configuration file
        with open(config_to_read, mode="rt", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        if not isinstance(config, dict):
            raise ValueError(f"Invalid serverless.yml template: {config_to_read}")

        config["service"] = self.instance.service_name  # Update the service name

        if not self.instance.functions:
            raise ValueError(
                "ServerlessFrameworkGenerator requires at least one function"
            )

        runtime = str(self.instance.functions[0].runtime)
        config["provider"]["runtime"] = runtime  # Update the runtime

        if self.instance.env:
            config["provider"]["env"] = self.instance.env
        if self.instance.secret:
            config["provider"]["secret"] = self.instance.secret

        config["functions"] = {
            function.name: {} for function in self.instance.functions
        }
        for function in self.instance.functions:  # Iterate over the functions
            config["functions"][
                function.name
            ] = _ServerlessFrameworkFunction.from_function(function).asdict()

        with open(config_path, mode="wt", encoding="utf-8") as file:
            yaml.dump(config, file)  # Write serverless.yml
