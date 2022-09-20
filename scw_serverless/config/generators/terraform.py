import hashlib
import json
import os
import sys
from zipfile import ZipFile


class TerraformGenerator:
    """
    Terraform Generator

    This class is responsible for generating Terraform Configuration
    """

    def __init__(self, instance):
        self.instance = instance

    def list_files(self, source):
        zip_files = []

        for path, subdirs, files in os.walk(source):
            for name in files:
                zip_files.append(os.path.join(path, name))

        return zip_files

    def create_zip_file(self, zip_path, source):
        files = self.list_files(source)

        with ZipFile(zip_path, "w") as zip:
            for file in files:
                zip.write(file)

    def add_args(self, config, args):
        allowed_args = [  # List of allowed args in terraform function configuration
            "min_scale",
            "max_scale",
            "memory_limit",
            "timeout",
            "privacy",
            "description",
        ]

        for k, v in args.items():
            if k in allowed_args:
                config[k] = v

    def write(self, path):
        version = f"{sys.version_info.major}{sys.version_info.minor}"  # Get the python version from the current env
        config_path = os.path.join(path, "terraform.tf.json")

        config_to_read = config_path

        if not os.path.exists(config_path):
            config_to_read = os.path.join(
                os.path.dirname(__file__), "..", "templates", "terraform.tf.json"
            )

        with open(config_to_read, "r") as file:
            config = json.load(file)

        self.create_zip_file(f"{path}/functions.zip", "./")
        with open(f"{path}/functions.zip", "rb") as f:
            zip_bytes = f.read()
            zip_hash = hashlib.sha256(zip_bytes).hexdigest()

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
            config["resource"]["scaleway_function"][func["function_name"]] = {
                "namespace_id": "${scaleway_function_namespace.main.id}",
                "runtime": f"python{version}",
                "handler": func["handler"],
                "name": func["function_name"],
                "zip": "functions.zip",
                "zip_hash": zip_hash,
                "deploy": True,
            }
            self.add_args(
                config["resource"]["scaleway_function"][func["function_name"]],
                func["args"],
            )

        functions = list(
            map(lambda x: x["function_name"], self.instance.functions)
        )  # create a list containing the functions name

        config["resource"]["scaleway_function"] = {
            key: val
            for key, val in config["resource"]["scaleway_function"].items()
            if key in functions
        }  # remove not present functions from configuration file

        with open(config_path, "w") as file:
            json.dump(config, file, indent=2)
