import os
import shutil
import subprocess

import requests
from requests.adapters import HTTPAdapter, Retry
from scaleway import Client

from tests import constants

CLI_COMMAND = "scw-serverless"


def create_client() -> Client:
    client = Client.from_config_file_and_env()
    if not client.default_region:
        client.default_region = constants.DEFAULT_REGION
    client.validate()
    return client


def run_cli(client: Client, directory: str, args: list[str]):
    cli = shutil.which(CLI_COMMAND)
    assert cli
    return subprocess.run(
        [cli] + args,
        env={
            "SCW_SECRET_KEY": client.secret_key,
            "SCW_ACCESS_KEY": client.access_key,
            "SCW_DEFAULT_PROJECT_ID": client.default_project_id,
            "SCW_DEFAULT_REGION": client.default_region,
            "PATH": os.environ["PATH"],
        },  # type: ignore // client already validated
        capture_output=True,
        cwd=directory,
        check=False,  # Checked in the tests
    )


def trigger_function(url: str, max_retries: int = 5) -> requests.Response:
    session = requests.Session()
    retries = Retry(total=max_retries, backoff_factor=0.1)
    session.mount("https://", HTTPAdapter(max_retries=retries))
    req = session.get(url, timeout=constants.COLD_START_TIMEOUT)
    req.raise_for_status()
    return req
