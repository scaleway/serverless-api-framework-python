import os
import random
import re
import shutil
import subprocess
import tempfile
import time
from typing import Iterable, List, Tuple

import pytest
import requests
import yaml
from requests import HTTPError
from scaleway import Client, load_profile_from_env
from scaleway.account.v2 import AccountV2API
from scaleway.function.v1beta1 import FunctionV1Beta1API
from scaleway.registry.v1 import RegistryV1API

from scw_serverless.utils.commands import get_command_path
from tests.utils import ROOT_PROJECT_DIR, TESTS_DIR

DEFAULT_REGION = "pl-waw"
CLI_COMMAND = "srvless"


def create_project(client: Client, suffix: str):
    sha = os.getenv("GITHUB_SHA", "local")
    name = f"apifw-{sha[:7]}-{suffix}-{random.randint(0, 9999)}"
    project = AccountV2API(client).create_project(name, os.getenv("SCW_ORG_ID"))
    return project.id


def delete_project(client: Client, project_id: str, max_tries: int = 5):
    api = AccountV2API(client)
    for _ in range(max_tries):
        try:
            api.delete_project(project_id=project_id)
            break
        # pylint: disable=broad-except # SDK only returns Exception
        except Exception:
            time.sleep(30)


def cleanup(client: Client, project_id: str):
    if os.path.exists("../.scw"):
        shutil.rmtree("../.scw")  # remove .scw/deployment.zip
    if os.path.exists("../.serverless"):
        shutil.rmtree("../.serverless")  # remove serverless framework files

    api = FunctionV1Beta1API(client)
    for namespace in api.list_namespaces_all(project_id=project_id):
        api.delete_namespace(namespace_id=namespace.id)

    registry_api = RegistryV1API(client)
    for registry in registry_api.list_namespaces_all(project_id=project_id):
        registry_api.delete_namespace(namespace_id=registry.id)

    print("Waiting for namespaces deletions...")
    for _ in range(30):
        namespaces = api.list_namespaces_all(project_id=project_id)
        registries = registry_api.list_namespaces_all(project_id=project_id)
        if not namespaces and not registries:
            break
        time.sleep(20)


def call_function(url: str, max_retries: int = 5):
    retry_delay = 5
    raised_ex = None

    for _ in range(max_retries):
        try:  # Call the function
            req = requests.get(url, timeout=retry_delay)
            req.raise_for_status()
            break
        except ConnectionError as exception:
            time.sleep(retry_delay)
            raised_ex = exception
        except HTTPError as exception:
            raised_ex = exception
            # If the request as timed out
            if exception.response.status_code != 408:
                break
            time.sleep(retry_delay)

    if raised_ex:
        raise raised_ex


def copy_project():
    directory = tempfile.mkdtemp()
    shutil.copytree(TESTS_DIR, os.path.join(directory, "tests"))
    return directory


def run_srvless_cli(project_id: str, args: List[str], cwd: str = TESTS_DIR):
    # Run the command line
    srvless_path = get_command_path(CLI_COMMAND)
    assert srvless_path

    return subprocess.run(
        [srvless_path] + args,
        env={
            # Should fail if SCW_SECRET_KEY is not defined
            "SCW_SECRET_KEY": os.environ["SCW_SECRET_KEY"],
            "SCW_ACCESS_KEY": os.environ["SCW_ACCESS_KEY"],
            "SCW_DEFAULT_PROJECT_ID": project_id,
            "SCW_REGION": DEFAULT_REGION,
            "PATH": os.environ["PATH"],
        },
        capture_output=True,
        # Runs the cli in the tests directory
        cwd=cwd,
        check=False,  # Checked in the tests
    )


def generate_scw_config():
    path = os.path.join(TESTS_DIR, "scw.yaml")
    with open(path, mode="w", encoding="utf-8") as fp:
        yaml.dump(
            {
                "access_key": os.getenv("SCW_ACCESS_KEY"),
                "secret_key": os.getenv("SCW_SECRET_KEY"),
                "default_region": DEFAULT_REGION,
            },
            fp,
        )
    return path


@pytest.fixture(name="serverless_project")
def _create_serverless_project() -> Iterable[Tuple[str, str]]:
    profile = load_profile_from_env()
    if not profile.default_region:
        profile.default_region = DEFAULT_REGION
    client = Client.from_profile(profile)
    project_id = create_project(client, "dpl")

    print(f"Using project: {project_id}")

    # Copy the whole project to a temporary directory
    project_dir = copy_project()

    try:
        yield (project_id, project_dir)
    finally:
        cleanup(client, project_id)
        delete_project(client, project_id)
        shutil.rmtree(project_dir)


def deploy(app_file: str, backend: str, serverless_project: Tuple[str, str]):
    (project_id, project_dir) = serverless_project
    app_file = app_file.replace(os.path.abspath(ROOT_PROJECT_DIR), project_dir)
    ret = run_srvless_cli(project_id, ["deploy", app_file, "-b", backend], project_dir)

    assert ret.returncode == 0, print(ret)

    output = str(ret.stdout.decode("UTF-8")).strip()
    if backend == "serverless":
        # serverless framework print normal output on stderr
        output = str(ret.stderr.decode("UTF-8")).strip()

    assert "Done! Functions have been successfully deployed!" in output, print(ret)

    output = str(ret.stdout.decode("UTF-8")).strip()
    pattern = re.compile(r"(Function [a-z0-9-]+ deployed to:? (https://.+))")

    groups = re.findall(pattern, output)

    for group in groups:
        # Call the actual function
        call_function(group[1])


def serverless_framework(app_file: str, serverless_project: Tuple[str, str]):
    (project_id, project_dir) = serverless_project
    app_file = app_file.replace(os.path.abspath(TESTS_DIR), project_dir)
    ret = run_srvless_cli(
        project_id, ["generate", app_file, "-t", "serverless"], project_dir
    )

    assert ret.returncode == 0, print(ret)
    assert "Done" in str(ret.stdout.decode("UTF-8")).strip(), print(ret)

    # Run the serverless Framework
    serverless_path = get_command_path("serverless")
    assert serverless_path

    node_path = get_command_path("node")
    assert node_path

    serverless = subprocess.run(
        [node_path, serverless_path, "deploy"],
        env={
            "SCW_SECRET_KEY": os.environ["SCW_SECRET_KEY"],
            "SCW_DEFAULT_PROJECT_ID": project_id,
            "SCW_REGION": DEFAULT_REGION,
        },
        capture_output=True,
        cwd=project_dir,
        check=False,
    )

    assert serverless.returncode == 0, print(serverless)
    assert (
        "Function hello-world has been deployed"
        in str(serverless.stderr.decode("UTF-8")).strip()
    ), print(serverless)

    output = str(serverless.stderr.decode("UTF-8")).strip()

    print(output)

    pattern = re.compile("(Function [a-z0-9-]+ has been deployed to: (https://.+))")
    groups = re.findall(pattern, output)

    for group in groups:
        # Call the actual function
        call_function(group[1])


def terraform(app_file: str, serverless_project: Tuple[str, str]):
    (project_id, project_dir) = serverless_project
    app_file = app_file.replace(os.path.abspath(ROOT_PROJECT_DIR), project_dir)
    ret = run_srvless_cli(
        project_id, ["generate", app_file, "-t", "terraform"], project_dir
    )

    assert ret.returncode == 0, print(ret)
    assert "Done" in str(ret.stdout.decode("UTF-8")).strip(), print(ret)

    # Run terraform
    terraform_path = get_command_path("terraform")
    assert terraform_path

    subprocess.run(
        [terraform_path, "init"], capture_output=True, cwd=project_dir, check=True
    )

    subprocess.run(
        [terraform_path, "validate"],
        env={
            "TF_VAR_project_id": project_id,
            "SCW_CONFIG_PATH": generate_scw_config(),
        },
        capture_output=True,
        check=True,
    )
