import os
import sys

import yaml


class ServerlessFrameworkGenerator:
    """
    Serverless Framework Generator

    This class is responsible for generating a serverless.yml config file
    """

    def __init__(self, instance):
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

        for func in self.instance.functions:  # Iterate over the functions
            if (
                func["function_name"] in config["functions"]
            ):  # The function is already configured, update the handler to make sure the correct one is used.
                config["functions"][func["function_name"]]["handler"] = func["handler"]
            else:
                config["functions"][func["function_name"]] = {
                    "handler": func["handler"],
                }

            # Set the correct events.
            config["functions"][func["function_name"]]["events"] = [
                {"http": {"path": func["url"], "method": "get"}}
            ]

        functions = list(
            map(lambda x: x["function_name"], self.instance.functions)
        )  # create a list containing the functions name

        config["functions"] = {
            key: val for key, val in config["functions"].items() if key in functions
        }  # remove not present functions from configuration file

        with open(config_path, "w") as file:
            yaml.dump(config, file)  # Write serverless.yml
