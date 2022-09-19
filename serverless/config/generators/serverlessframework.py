import os
import sys

import yaml

from serverless.app import Serverless


class ServerlessFrameworkGenerator:
    """
    Serverless Framework Generator

    This class is responsible for generating a serverless.yml config file
    """

    def __init__(self, instance: Serverless):
        self.instance = instance

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

        for func in self.instance.functions:  # Iterate over the functions
            func.add_func_to_config(config)

        functions = [fun.name for fun in self.instance.functions]
        config["functions"] = {
            key: val for key, val in config["functions"].items() if key in functions
        }  # remove not present functions from configuration file

        with open(config_path, "w") as file:
            yaml.dump(config, file)  # Write serverless.yml
