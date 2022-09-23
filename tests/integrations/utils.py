import os
import re
import shutil
import subprocess
import time

import requests

from scw_serverless.utils.commands import get_command_path

REGION = "fr-par"
API_URL = "https://api.scaleway.com"
FUNCTIONS_BASE_URL = f"{API_URL}/functions/v1beta1/regions/{REGION}"
ACCOUNT_BASE_URL = f"{API_URL}/account/v2/projects"
REGISTRY_BASE_URL = f"{API_URL}/registry/v1/regions/{REGION}"
HEADERS = {"X-Auth-Token": os.getenv("SCW_SECRET_KEY")}


def create_project(suffix: str):
    sha = os.getenv("GITHUB_SHA")
    if sha is None:
        sha = "local"
    req = requests.post(
        ACCOUNT_BASE_URL,
        json={
            "name": f"apifw-{sha[:7]}-{suffix}",
            "organization_id": os.getenv("SCW_ORG_ID"),
        },
        headers=HEADERS,
    )

    req.raise_for_status()

    return req.json()["id"]


def delete_project(project_id, retries: int = 0):
    req = requests.delete(
        f"{ACCOUNT_BASE_URL}/{project_id}",
        headers=HEADERS,
    )

    if req.status_code == 400 and retries <= 3:
        time.sleep(42)
        return delete_project(project_id, retries + 1)

    req.raise_for_status()


def cleanup(project_id):
    if os.path.exists("../.scw"):
        shutil.rmtree("../.scw")  # remove .scw/deployment.zip
    if os.path.exists("../.serverless"):
        shutil.rmtree("../.serverless")  # remove serverless framework files

    namespaces = requests.get(
        f"{FUNCTIONS_BASE_URL}/namespaces?project_id={project_id}",
        headers=HEADERS,
    )  # List namespaces
    namespaces.raise_for_status()
    for namespace in namespaces.json()["namespaces"]:
        delete_namespace = requests.delete(
            f"{FUNCTIONS_BASE_URL}/namespaces/{namespace['id']}",
            headers=HEADERS,
        )  # Delete namespace
        delete_namespace.raise_for_status()
    time.sleep(60)  # wait for resource deletion
    registries = requests.get(
        f"{REGISTRY_BASE_URL}/namespaces?project_id={project_id}",
        headers=HEADERS,
    )  # List containers registries
    registries.raise_for_status()
    for registry in registries.json()["namespaces"]:
        delete_registry = requests.delete(
            f"{REGISTRY_BASE_URL}/namespaces/{registry['id']}",
            headers=HEADERS,
        )  # Delete container registry
        delete_registry.raise_for_status()


def call_function(url: str, retries: int = 0):
    try:
        # Call the function
        req = requests.get(url)
        req.raise_for_status()
    except ConnectionError:
        if retries <= 3:
            time.sleep(42)
            # retry calling the function
            return call_function(url, retries + 1)
        # Already retried without success abort.
        raise ConnectionError


def deploy(
    file: str, do_cleanup: bool = True, project_id: str = None, backend: str = "api"
):
    if project_id is None:
        project_id = create_project("dpl")

    try:
        srvlss_path = get_command_path("srvlss")
        assert srvlss_path is not None

        ret = subprocess.run(
            [
                srvlss_path,
                "deploy",
                "-f",
                file,
                "-b",
                backend,
            ],
            env={
                "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
                "SCW_DEFAULT_PROJECT_ID": project_id,
            },
            capture_output=True,
            cwd="../",
        )

        assert ret.returncode == 0
        assert (
            "Function hello-world has been deployed"
            in str(ret.stdout.decode("UTF-8")).strip()
        )
        assert "Status is in error state" not in str(ret.stdout.decode("UTF-8")).strip()

        output = str(ret.stdout.decode("UTF-8")).strip()
        pattern = re.compile(
            "(Function [a-z0-9-]+ has been deployed to:? (https://.+))"
        )

        groups = re.findall(pattern, output)

        for group in groups:
            # Call the actual function
            call_function(group[1])

    finally:
        if do_cleanup:
            cleanup(project_id)
            delete_project(project_id)
    return project_id


def serverless_framework(file: str, do_cleanup: bool = True, project_id: str = None):
    if project_id is None:
        project_id = create_project("slfw")

    try:
        # Run the command line
        srvlss_path = get_command_path("srvlss")
        assert srvlss_path is not None

        ret = subprocess.run(
            [
                srvlss_path,
                "generate",
                "-t",
                "serverless",
                "-f",
                file,
            ],
            env={
                "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
                "SCW_DEFAULT_PROJECT_ID": project_id,
                "SCW_REGION": REGION,
            },
            capture_output=True,
            cwd="../",
        )

        assert ret.returncode == 0
        assert "Done" in str(ret.stdout.decode("UTF-8")).strip()

        # Run the serverless Framework

        serverless_path = get_command_path("serverless")
        assert serverless_path is not None

        node_path = get_command_path("node")
        assert node_path is not None

        serverless = subprocess.run(
            [
                node_path,
                serverless_path,
                "deploy",
            ],
            env={
                "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
                "SCW_DEFAULT_PROJECT_ID": project_id,
                "SCW_REGION": REGION,
            },
            capture_output=True,
            cwd="../",
        )

        assert serverless.returncode == 0
        assert (
            "Function hello-world has been deployed"
            in str(serverless.stderr.decode("UTF-8")).strip()
        )

        output = str(serverless.stderr.decode("UTF-8")).strip()

        print(output)

        pattern = re.compile("(Function [a-z0-9-]+ has been deployed to: (https://.+))")
        groups = re.findall(pattern, output)

        for group in groups:
            # Call the actual function
            call_function(group[1])

    finally:
        if do_cleanup:
            cleanup(project_id)
            delete_project(project_id)
    return project_id
