import os
import random
import re
import shutil
import subprocess
import time
from typing import List

import requests
import yaml
from requests import HTTPError

from scw_serverless.utils.commands import get_command_path
from tests.utils import ROOT_PROJECT_DIR, TESTS_DIR
from tests.utils import request_scw_api

REGION = "pl-waw"
API_URL = "https://api.scaleway.com"
FUNCTIONS_BASE_URL = f"functions/v1beta1/regions/{REGION}"
ACCOUNT_BASE_URL = f"account/v2/projects"
REGISTRY_BASE_URL = f"registry/v1/regions/{REGION}"
HEADERS = {"X-Auth-Token": os.getenv("SCW_SECRET_KEY")}


def create_project(suffix: str):
    sha = os.getenv("GITHUB_SHA")
    if sha is None:
        sha = "local"
    resp = request_scw_api(
        route=ACCOUNT_BASE_URL,
        method="POST",
        json={
            "name": f"apifw-{sha[:7]}-{suffix}_{str(random.randint(0, 9999))}",
            "organization_id": os.getenv("SCW_ORG_ID"),
        },
    )

    return resp.json()["id"]


def delete_project(project_id, retries: int = 0):
    req = requests.delete(
        f"{API_URL}/{ACCOUNT_BASE_URL}/{project_id}",
        headers=HEADERS,
    )

    if req.status_code == 400 and retries <= 3:
        time.sleep(42)
        return delete_project(project_id, retries + 1)

    # ignoring the error.
    # req.raise_for_status()


def cleanup(project_id):
    if os.path.exists("../.scw"):
        shutil.rmtree("../.scw")  # remove .scw/deployment.zip
    if os.path.exists("../.serverless"):
        shutil.rmtree("../.serverless")  # remove serverless framework files

    # List namespaces
    namespaces = request_scw_api(
        route=f"{FUNCTIONS_BASE_URL}/namespaces?project_id={project_id}"
    )
    for namespace in namespaces.json()["namespaces"]:
        # Delete namespace
        request_scw_api(
            route=f"{FUNCTIONS_BASE_URL}/namespaces/{namespace['id']}", method="DELETE"
        )
    # wait for resource deletion
    time.sleep(60)
    # List containers registries
    registries = request_scw_api(
        route=f"{REGISTRY_BASE_URL}/namespaces?project_id={project_id}"
    )
    for registry in registries.json()["namespaces"]:
        # Delete container registry
        request_scw_api(
            route=f"{REGISTRY_BASE_URL}/namespaces/{registry['id']}", method="DELETE"
        )


def call_function(url: str):
    retries = 0
    retry_delay = 42
    raised_ex = None

    while retries < 3:
        try:
            # Call the function
            req = requests.get(url)
            req.raise_for_status()

            raised_ex = None
            # No exception raised. Call was successful
            break
        except ConnectionError as ex:
            time.sleep(retry_delay)
            retries += 1
            raised_ex = ex
        except HTTPError as ex:
            raised_ex = ex

            # If the request as timed out
            if ex.response.status_code == 408:
                time.sleep(retry_delay)
                retries += 1
            else:
                # The request has not timed out. The function deployment was unsuccessful
                break

    if raised_ex:
        raise raised_ex


def copy_project(project_id: str):
    directory = f"/tmp/apifw_{project_id}"
    if not os.path.exists(directory):
        shutil.copytree(ROOT_PROJECT_DIR, directory)

    return directory


def run_srvlss_cli(project_id: str, args: List[str], cwd: str = TESTS_DIR):
    # Run the command line
    srvlss_path = get_command_path("srvlss")
    assert srvlss_path is not None

    return subprocess.run(
        [srvlss_path] + args,
        env={
            "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
            "SCW_DEFAULT_PROJECT_ID": project_id,
            "SCW_REGION": REGION,
        },
        capture_output=True,
        # Runs the cli in the tests directory
        cwd=cwd,
    )


def generate_scw_config():
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
    return path


def deploy(
    file: str, do_cleanup: bool = True, project_id: str = None, backend: str = "api"
):
    if project_id is None:
        project_id = create_project("dpl")

    print(f"Using project: {project_id}")

    # Copy the whole project to a temporary directory
    project_dir = copy_project(project_id=project_id)
    file = file.replace(os.path.abspath(ROOT_PROJECT_DIR), project_dir)

    try:
        srvlss_path = get_command_path("srvlss")
        assert srvlss_path is not None

        ret = subprocess.run(
            [srvlss_path, "deploy", "-f", file, "-b", backend, "--region", "pl-waw"],
            env={
                "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
                "SCW_DEFAULT_PROJECT_ID": project_id,
                "PATH": os.getenv("PATH"),
            },
            capture_output=True,
            cwd=project_dir,
        )

        assert ret.returncode == 0, print(ret)

        output = str(ret.stdout.decode("UTF-8")).strip()
        if backend == "serverless":
            # serverless framework print normal output on stderr
            output = str(ret.stderr.decode("UTF-8")).strip()

        assert "Function hello-world has been deployed" in output, print(ret)
        assert (
            "Status is in error state" not in str(ret.stdout.decode("UTF-8")).strip()
        ), print(ret)

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
            shutil.rmtree(project_dir)
    return project_id


def serverless_framework(file: str, do_cleanup: bool = True, project_id: str = None):
    if project_id is None:
        project_id = create_project("slfw")

    print(f"Using project: {project_id}")

    # Copy the whole project to a temporary directory
    project_dir = copy_project(project_id=project_id)
    file = file.replace(os.path.abspath(ROOT_PROJECT_DIR), project_dir)

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
            cwd=project_dir,
        )

        assert ret.returncode == 0, print(ret)
        assert "Done" in str(ret.stdout.decode("UTF-8")).strip(), print(ret)

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
            cwd=project_dir,
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

    finally:
        if do_cleanup:
            cleanup(project_id)
            delete_project(project_id)
            shutil.rmtree(project_dir)
    return project_id


def terraform(file: str, do_cleanup: bool = True, project_id: str = None):
    if project_id is None:
        project_id = create_project("slfw")

    print(f"Using project: {project_id}")

    # Copy the whole project to a temporary directory
    project_dir = copy_project(project_id=project_id)
    file = file.replace(os.path.abspath(ROOT_PROJECT_DIR), project_dir)

    try:
        # Run the command line
        srvlss_path = get_command_path("srvlss")
        assert srvlss_path is not None

        ret = subprocess.run(
            [
                srvlss_path,
                "generate",
                "-t",
                "terraform",
                "-f",
                file,
            ],
            env={
                "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
                "SCW_DEFAULT_PROJECT_ID": project_id,
                "SCW_REGION": REGION,
            },
            capture_output=True,
            cwd=project_dir,
        )

        assert ret.returncode == 0, print(ret)
        assert "Done" in str(ret.stdout.decode("UTF-8")).strip(), print(ret)

        # Run terraform

        terraform_path = get_command_path("terraform")
        assert terraform_path is not None

        with open(os.path.join(TESTS_DIR, "output.tf"), "w") as fp:
            fp.write(
                """
output "domain_name" {
  value = scaleway_function.hello-world.domain_name
}
            """
            )

        subprocess.run([terraform_path, "init"], capture_output=True, cwd=project_dir)

        tf_apply = subprocess.run(
            [terraform_path, "apply", "-auto-approve"],
            env={
                "TF_VAR_project_id": project_id,
                "SCW_CONFIG_PATH": generate_scw_config(),
            },
            capture_output=True,
            cwd=project_dir,
        )

        assert tf_apply.returncode == 0, print(tf_apply)
        assert "Apply complete!" in str(tf_apply.stdout.decode("UTF-8")).strip(), print(
            tf_apply
        )

        tf_out = subprocess.run(
            [terraform_path, "output", "domain_name"],
            capture_output=True,
            cwd=project_dir,
        )
        url = "https://" + tf_out.stdout.decode("UTF-8").strip().strip('"')
        call_function(url)

    finally:
        if do_cleanup:
            cleanup(project_id)
            delete_project(project_id)
            shutil.rmtree(project_dir)
    return project_id
