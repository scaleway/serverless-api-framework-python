import json
import os
import sys


class TerraformGenerator:
    """
    Terraform Generator

    This class is responsible for generating Terraform Configuration
    """

    def __init__(self, instance):
        self.instance = instance

    def write(self, path):
        version = f"{sys.version_info.major}{sys.version_info.minor}"  # Get the python version from the current env
        config_path = os.path.join(path, "serverless.yml")

        config_to_read = config_path

        if not os.path.exists(config_path):
            config_to_read = os.path.join(
                os.path.dirname(__file__), "..", "templates", "terraform.tf.json"
            )

        with open(config_to_read, "r") as file:
            config = json.load(file)

        config["resource"]["scaleway_function_namespace"] = {
            self.instance.service_name: {
                "name": f"{self.instance.service_name}-function-namespace",
                "description": f"{self.instance.service_name} function namespace",
            }
        }

        if self.instance.env is not None:
            config["resource"]["scaleway_function_namespace"][
                self.instance.service_name
            ]["environment_variables"] = self.instance.env

        config["resource"]["scaleway_function"] = {}

        for func in self.instance.functions:  # Iterate over the functions
            pass

        with open(config_path, "w") as file:
            json.dump(config, file, indent=2)

        # for func in self.instance.functions:  # Iterate over the functions
        #     if (
        #             func["function_name"] in config["functions"]
        #     ):  # The function is already configured, update the handler to make sure the correct one is used.
        #         config["functions"][func["function_name"]]["handler"] = func["handler"]
        #     else:
        #         config["functions"][func["function_name"]] = {
        #             "handler": func["handler"],
        #         }
        #
        #     self.add_args(config["functions"][func["function_name"]], func["args"])
        #     # Set the correct events.
        #     # config["functions"][func["function_name"]]["events"] = [
        #     #     {"http": {"path": func["url"], "method": "get"}}
        #     # ]
        #
        # functions = list(
        #     map(lambda x: x["function_name"], self.instance.functions)
        # )  # create a list containing the functions name
        #
        # config["functions"] = {
        #     key: val for key, val in config["functions"].items() if key in functions
        # }  # remove not present functions from configuration file
        #
        # with open(config_path, "w") as file:
        #     yaml.dump(config, file)  # Write serverless.yml
