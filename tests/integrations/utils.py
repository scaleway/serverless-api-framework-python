import os
import shutil
import time
from pathlib import Path
from types import ModuleType
from typing import Optional

import requests
import scaleway.function.v1beta1 as sdk
from click.testing import CliRunner, Result
from requests.adapters import HTTPAdapter, Retry
from scaleway import Client

from scw_serverless.app import Serverless
from scw_serverless.cli import deploy
from tests import constants

RETRY_INTERVAL = 10


def create_client(project_id: Optional[str] = None) -> Client:
    client = Client.from_config_file_and_env()
    if not client.default_region:
        client.default_region = constants.DEFAULT_REGION
    client.validate()
    if project_id:
        client.default_project_id = project_id
    return client


def run_deploy_command(
    cli_runner: CliRunner, app: ModuleType, args: Optional[list[str]] = None
) -> Result:
    assert app.__file__
    app_path = Path(app.__file__)
    cwd = Path(os.getcwd())
    shutil.copytree(
        src=app_path.parent,
        dst=cwd,
        dirs_exist_ok=True,
    )

    return cli_runner.invoke(
        deploy,
        args=(args or []) + [str(cwd / app_path.name)],
        # When vendoring scw-serverless to install it on Scaleway Functions,
        # we use the version being tested. This is achieved by passing the absolute path
        # to the project in the requirements.txt file.
        env={"SCW_SERVERLESS_FOLDER": str(constants.PROJECT_DIR)},
        catch_exceptions=False,
    )


def get_deployed_functions_by_name(client: Client, app_instance: Serverless):
    api = sdk.FunctionV1Beta1API(client)
    namespaces = api.list_namespaces_all(name=app_instance.service_name)
    assert namespaces
    deployed_functions = api.list_functions_all(namespace_id=namespaces[0].id)
    return {function.name: function for function in deployed_functions}


def trigger_function(domain_name: str, max_retries: int = 10) -> requests.Response:
    url = f"https://{domain_name}"
    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=2,
        status=max_retries,  # Status max retries
        status_forcelist=[500, 404],
        raise_on_status=False,  # Raise for status called after
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    req = session.get(url, timeout=constants.COLD_START_TIMEOUT)
    req.raise_for_status()
    return req


def wait_for_body_text(
    domain_name: str, body: str, max_retries: int = 20
) -> requests.Response:
    last_body = None
    for _ in range(max_retries):
        resp = trigger_function(domain_name)
        if resp.text == body:
            return resp
        last_body = resp.text
        time.sleep(RETRY_INTERVAL)
    raise RuntimeError(
        f"Max retries {max_retries} for {domain_name} to match {body}, got: {last_body}"
    )
