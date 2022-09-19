class Serverless:
    def __init__(self, service_name: str, env: dict = None, secret: dict = None):
        self.functions = []
        self.service_name = service_name
        self.env = env
        self.secret = secret

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

    def nomalize_function_name(self, name):
        return name.lower().replace("_", "-")

    def func(self, **kwargs):
        """
        @func decorator

        :param kwargs:
        :return:
        """

        def decorator(handler):
            self.functions.append(
                {
                    "function_name": self.nomalize_function_name(handler.__name__),
                    # FIXME: Using the function name may result in some function not being save if their name is
                    #  duplicated.
                    "handler": f"{self.module_to_path(handler.__module__)}.{handler.__name__}",
                    "args": kwargs,
                }
            )

            def _inner(*args, **kwargs):
                return handler(args, kwargs)

            return _inner

        return decorator
