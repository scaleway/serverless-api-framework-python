import sys

import yaml


class App:
    def __init__(self, service_name):
        self.functions = []
        self.service_name = service_name

    def module_to_path(self, module: str):
        """
        Replace dots by slash in the module name

        :param module:
        :return:
        """
        return module.replace(
            ".", "/"
        )  # This may break in certain scenarios need to test it. For example if your
        # serverless framework is not at the root of you project.

    def func(self, **kwargs):
        """
        @func decorator

        :param kwargs:
        :return:
        """

        def decorator(handler):
    self.functions.append(
        {
            "function_name": handler.__name__,
            "handler": f"{self.module_to_path(handler.__module__)}.{handler.__name__}",
            "url": kwargs.get("url"),
        }
    )

    def _inner(*args, **kwargs):
        return handler(args, kwargs)

    return _inner

        return decorator

    def write_serverless_framework_yaml(self):
        version = f"{sys.version_info.major}{sys.version_info.minor}"  # Get the python version from the current env
        config = {
            "service": self.service_name,
            "configValidationMode": "off",
            "provider": {
                "name": "scaleway",
                "runtime": f"python{version}",
                "scwToken": "${env:SCW_SECRET_KEY}",
                "scwProject": "${env:SCW_DEFAULT_PROJECT_ID}",
                "scwRegion": "${env:SCW_REGION}",
                "env": {"test": "test"},
            },
            "plugins": ["serverless-scaleway-functions"],
            "package": {"patterns": ["!node_modules/**", "!.gitignore", "!.git/**"]},
            "functions": {},
        }

        functions = {}
        for func in self.functions:
            functions[func["function_name"]] = {
    "handler": func["handler"],
    "env": {"local": "local"},
    "events": [{"http": {"path": func["url"], "method": "get"}}],
}

        config["functions"] = functions

        with open("serverless.yml", "w") as file:
            yaml.dump(config, file)
