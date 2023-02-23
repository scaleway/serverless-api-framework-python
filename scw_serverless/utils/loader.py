import importlib.util
import inspect
import sys
from pathlib import Path

from scw_serverless.app import Serverless


def get_module_name(file: Path) -> str:
    """Extract the module name from the path."""

    file = file.resolve()
    return (
        str(file.relative_to(Path(".").resolve())).removesuffix(".py").replace("/", ".")
    )


def get_app_instance(file: Path) -> Serverless:
    """Load the app instance from the client module."""

    module_name = get_module_name(file)
    parent_directory = str(file.parent.resolve())

    spec = importlib.util.spec_from_file_location(
        module_name,
        str(file.resolve()),
        submodule_search_locations=[parent_directory],
    )

    if not spec or not spec.loader:
        raise ImportError(
            f"Can't find module {module_name} at location {file.resolve()}"
        )

    user_app = importlib.util.module_from_spec(spec)
    sys.path.append(parent_directory)
    sys.modules[module_name] = user_app
    spec.loader.exec_module(user_app)

    app_instance = None
    for member in inspect.getmembers(user_app):
        if isinstance(member[1], Serverless):
            # Ok. Found the variable now, need to use it
            app_instance = member[1]

    if not app_instance:  # No variable with type "Serverless" found
        raise RuntimeError(
            f"""Unable to locate an instance of serverless App
            in the provided file: {file}."""
        )

    return app_instance
