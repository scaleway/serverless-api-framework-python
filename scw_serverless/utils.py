import os
import subprocess
from pathlib import Path
from zipfile import ZipFile

import yaml

from scw_serverless.logger import get_logger


def list_files(source):
    zip_files = []

    for path, subdirs, files in os.walk(source):
        for name in files:
            zip_files.append(os.path.join(path, name))

    return zip_files


def create_zip_file(zip_path, source):
    files = list_files(source)

    with ZipFile(zip_path, "w", strict_timestamps=False) as zip:
        for file in files:
            zip.write(file)


def find_scw_credentials():
    if (
        os.getenv("SCW_SECRET_KEY") is not None
        and os.getenv("SCW_DEFAULT_PROJECT_ID") is not None
    ):
        get_logger().default("Using credentials from system environment")
        return os.getenv("SCW_SECRET_KEY"), os.getenv("SCW_DEFAULT_PROJECT_ID"), None
    elif os.path.exists(f"{str(Path.home())}/.config/scw/config.yaml"):
        config = {
            "secret_key": None,
            "default_project_id": None,
            "default_region": None,
        }
        with open(f"{str(Path.home())}/.config/scw/config.yaml", "r") as file:
            config = yaml.safe_load(file)

        if (
            config["secret_key"] is not None
            and config["default_project_id"] is not None
        ):
            get_logger().default(
                f"Using credentials from {str(Path.home())}/.config/scw/config.yaml"
            )

            return (
                config["secret_key"],
                config["default_project_id"],
                config["default_region"],
            )
    else:
        get_logger().error(
            "Unable to locate credentials",
        )

        return None, None, None


def check_if_installed(command: str):
    ret = subprocess.run(["which", command], capture_output=True)
    return ret.returncode == 0
