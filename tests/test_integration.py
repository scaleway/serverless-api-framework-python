from typing import List

import os
import re
import subprocess
import time
from urllib.parse import urljoin

import requests
import yaml
import pytest

from utils import request_scw_api, APP_PY_PATH, TESTS_DIR, SCALEWAY_API_URL

REGION = "fr-par"


def create_project():
    sha = os.getenv("GITHUB_SHA")
    if sha is None:
        sha = "local"
    req = request_scw_api(
        "account/v2/projects",
        method="POST",
        json={"name": f"apifw-{sha}", "organization_id": os.getenv("SCW_ORG_ID")},
    )
    return req.json()["id"]


def delete_project(project_id, retries: int = 0):
    req = requests.delete(
        urljoin(SCALEWAY_API_URL, f"account/v2/projects/{project_id}"),
        headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
    )
    if req.status_code == 400 and retries <= 3:
        time.sleep(42)
        return delete_project(project_id, retries + 1)


def cleanup(project_id):
    namespaces = request_scw_api(
        f"functions/v1beta1/regions/{REGION}/namespaces?project_id={project_id}"
    )
    for namespace in namespaces.json()["namespaces"]:
        request_scw_api(
            f"functions/v1beta1/regions/{REGION}/namespaces/{namespace['id']}",
            method="DELETE",
        )  # Delete namespace
    deleted = False
    while not deleted:
        response = request_scw_api(
            f"functions/v1beta1/regions/{REGION}/namespaces?project_id={project_id}"
        )
        if response.json()["namespaces"] == []:
            deleted = True
        time.sleep(1)
    registries = request_scw_api(
        f"registry/v1/regions/{REGION}/namespaces?project_id={project_id}",
    )  # List containers registries
    for registry in registries.json()["namespaces"]:
        request_scw_api(
            f"registry/v1/regions/{REGION}/namespaces/{registry['id']}", method="DELETE"
        )  # Delete container registry


def call_function(url: str, retries: int = 0):
    try:
        req = requests.get(url)  # Call the request
        req.raise_for_status()
    except ConnectionError:
        if retries <= 3:
            time.sleep(42)
            return call_function(url, retries + 1)  # retry calling the function
        raise ConnectionError  # Already retried without success abort.


@pytest.fixture(name="project_id")
def create_serverless_project_fixture():
    project_id = create_project()
    try:
        yield project_id
    finally:
        cleanup(project_id)
        delete_project(project_id)


def run_srvlss_cli(project_id: str, args: List[str]):
    # Run the command line
    which = subprocess.run(["which", "srvlss"], capture_output=True)

    return subprocess.run(
        [str(which.stdout.decode("UTF-8")).strip()] + args,
        env={
            "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
            "SCW_DEFAULT_PROJECT_ID": project_id,
            "SCW_REGION": REGION,
        },
        capture_output=True,
        # Runs the cli in the tests directory
        cwd=TESTS_DIR,
    )


def test_integration_serverless_framework(project_id):
    ret = run_srvlss_cli(
        project_id,
        ["generate", "-t", "serverless", "-f", "tests/dev/app.py"],
    )

    assert ret.returncode == 0
    assert "Done" in str(ret.stdout.decode("UTF-8")).strip()

    # Run the serverless Framework

    serverless_which = subprocess.run(["which", "serverless"], capture_output=True)
    node_which = subprocess.run(["which", "node"], capture_output=True)

    serverless = subprocess.run(
        [
            str(node_which.stdout.decode("UTF-8")).strip(),
            str(serverless_which.stdout.decode("UTF-8")).strip(),
            "deploy",
        ],
        env={
            "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
            "SCW_DEFAULT_PROJECT_ID": project_id,
            "SCW_REGION": REGION,
        },
        capture_output=True,
        cwd=TESTS_DIR,
    )

    assert serverless.returncode == 0
    assert (
        "Function hello-world has been deployed"
        in str(serverless.stderr.decode("UTF-8")).strip()
    )

    output = str(serverless.stderr.decode("UTF-8")).strip()
    pattern = re.compile("(Function [a-z0-9-]+ has been deployed to: (https://.+))")
    groups = re.search(pattern, output).groups()

    # Call the actual function
    call_function(groups[1])


@pytest.fixture(name="scw_config_path")
def generate_scw_config_fixture():
    path = os.path.join(TESTS_DIR, "scw.yaml")
    with open(path, "w") as fp:
        yaml.dump(
            {
                "access_key": os.getenv("SCW_ACCESS_KEY"),
                "secret_key": os.getenv("SCW_SECRET_KEY"),
                "default_region": REGION,
            },
            fp,
        )
    try:
        yield path
    finally:
        os.remove(path)


def test_integration_terraform(project_id, scw_config_path):
    ret = run_srvlss_cli(
        project_id,
        ["generate", "-t", "terraform", "-f", APP_PY_PATH],
    )
    try:
        assert ret.returncode == 0
        assert "Done" in str(ret.stdout.decode("UTF-8")).strip()

        terraform_which = subprocess.run(["which", "terraform"], capture_output=True)
        terraform_cmd = str(terraform_which.stdout.decode("UTF-8")).strip()

        subprocess.run([terraform_cmd, "init"], capture_output=True, cwd=TESTS_DIR)

        tf_apply = subprocess.run(
            [terraform_cmd, "apply", "-auto-approve"],
            env={
                "TF_VAR_project_id": project_id,
                "SCW_CONFIG_PATH": scw_config_path,
            },
            capture_output=True,
            cwd=TESTS_DIR,
        )

        assert tf_apply.returncode == 0
        assert "Apply complete!" in str(tf_apply.stdout.decode("UTF-8")).strip()
    finally:
        should_be_deleted = [
            "terraform.tf.json",
            "functions.zip",
            "terraform.tfstate",
            ".terraform.lock.hcl",
        ]
        for file in should_be_deleted:
            os.remove(os.path.join(TESTS_DIR, file))
