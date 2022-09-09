import sys

import yaml


class App:
    def __init__(self, service_name):
        self.functions = []
        self.service_name = service_name

    def func(self, **kwargs):
        def decorator(handler):
            self.functions.append({
                "function_name": handler.__name__,
                "handler": f"{handler.__module__}.{handler.__name__}",
                "url": kwargs.get("url")
            })

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return decorator

    def get_functions(self):
        return self.functions

    def write_yaml(self):
        with open('test.yaml', 'w') as file:
            yaml.dump(self.functions, file)

    def write_serverless_framework_yaml(self):
        version = f"{sys.version_info.major}{sys.version_info.minor}"
        config = {
            "service": self.service_name,
            "configValidationMode": "off",
            "provider": {
                "name": "scaleway",
                "runtime": f"python{version}",
                "env": {
                    "test": "test"
                }
            },
            "plugins": [
                "serverless-scaleway-functions"
            ],
            "package": {
                "patterns": [
                    "!node_modules/**",
                    "!.gitignore",
                    "!.git/**"
                ]
            },
            "functions": {}
        }

        functions = {}
        for func in self.functions:
            print(func)
            functions[func["function_name"]] = {
                "handler": func["handler"],
                "env": {
                    "local": "local"
                }
            }

        config["functions"] = functions

        with open('serverless.yml', 'w') as file:
            yaml.dump(config, file)
