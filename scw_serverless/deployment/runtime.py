import logging
import sys

from scaleway.function import v1beta1 as sdk


def get_current_runtime() -> sdk.FunctionRuntime:
    """Get the current Python version expressed as a runtime string."""
    runtime = sdk.FunctionRuntime.PYTHON310
    version = f"python{sys.version_info.major}{sys.version_info.minor}"
    try:
        runtime = sdk.FunctionRuntime(version)
    except ValueError:
        logging.warning(
            "Unsupported Python version: %s, selecting default runtime: %s",
            version,
            runtime,
        )
    return runtime
