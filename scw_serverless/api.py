from typing import Any, Optional

from .config.function import Function

def function_to_sdk_args(function: Function) -> dict[str, Any]:
    return {
        "name":func.name,
        "runtime"=f"python{self._get_python_version()}",
        handler=func.handler_path,
        privacy=fn_args.get("privacy", "unknown_privacy"),
        environment_variables=fn_args.get("env"),
        min_scale=fn_args.get("min_scale"),
        max_scale=fn_args.get("max_scale"),
        memory_limit=fn_args.get("memory_limit"),
        timeout=fn_args.get("timeout"),
        description=fn_args.get("description"),
        secret_environment_variables=[
            Secret(key, value)
            for key, value in fn_args.get("secrets", {}).items()
        ],
    }