import os
import re
import shutil
import subprocess
import time

import requests

REGION = "fr-par"


def create_project(suffix: str):
    sha = os.getenv("GITHUB_SHA")
    if sha is None:
        sha = "local"
    req = requests.post(
        "https://api.scaleway.com/account/v2/projects",
        json={
            "name": f"apifw-{sha[:7]}-{suffix}",
            "organization_id": os.getenv("SCW_ORG_ID"),
        },
        headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
    )

    req.raise_for_status()

    return req.json()["id"]


def delete_project(project_id, retries: int = 0):
    req = requests.delete(
        f"https://api.scaleway.com/account/v2/projects/{project_id}",
        headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
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
        f"https://api.scaleway.com/functions/v1beta1/regions/{REGION}/namespaces?project_id={project_id}",
        headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
    )  # List namespaces
    namespaces.raise_for_status()
    for namespace in namespaces.json()["namespaces"]:
        delete_namespace = requests.delete(
            f"https://api.scaleway.com/functions/v1beta1/regions/{REGION}/namespaces/{namespace['id']}",
            headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
        )  # Delete namespace
        delete_namespace.raise_for_status()
    time.sleep(60)  # wait for resource deletion
    registries = requests.get(
        f"https://api.scaleway.com/registry/v1/regions/{REGION}/namespaces?project_id={project_id}",
        headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
    )  # List containers registries
    registries.raise_for_status()
    for registry in registries.json()["namespaces"]:
        delete_registry = requests.delete(
            f"https://api.scaleway.com/registry/v1/regions/{REGION}/namespaces/{registry['id']}",
            headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
        )  # Delete container registry
        delete_registry.raise_for_status()


def call_function(url: str, retries: int = 0):
    try:
        req = requests.get(url)  # Call the request
        req.raise_for_status()
    except ConnectionError:
        if retries <= 3:
            time.sleep(42)
            return call_function(url, retries + 1)  # retry calling the function
        raise ConnectionError  # Already retried without success abort.


def deploy(file: str, do_cleanup: bool = True, project_id: str = None):
    if project_id is None:
        project_id = create_project("dpl")

    try:
        which = subprocess.run(["which", "srvlss"], capture_output=True)

        ret = subprocess.run(
            [
                str(which.stdout.decode("UTF-8")).strip(),
                "deploy",
                "-f",
                file,
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
        pattern = re.compile("(Function [a-z0-9-]+ has been deployed to (https://.+))")

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
        which = subprocess.run(["which", "srvlss"], capture_output=True)

        ret = subprocess.run(
            [
                str(which.stdout.decode("UTF-8")).strip(),
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


def test_integration_deploy():
    deploy("tests/dev/app.py")


def test_integration_deploy_multiple_functions():
    deploy("tests/dev/multiple-functions.py")


def test_integration_deploy_existing_function():
    project_id = deploy("tests/dev/app.py", do_cleanup=False)
    deploy("tests/dev/app.py", do_cleanup=True, project_id=project_id)


def test_integration_deploy_multiple_existing_functions():
    project_id = deploy("tests/dev/multiple-functions.py", do_cleanup=False)
    deploy("tests/dev/multiple-functions.py", do_cleanup=True, project_id=project_id)


def test_integration_deploy_one_existing_function():
    project_id = deploy("tests/dev/app.py", do_cleanup=False)
    deploy("tests/dev/multiple-functions.py", do_cleanup=True, project_id=project_id)


def test_integration_serverless_framework():
    serverless_framework("tests/dev/app.py")


def test_integration_serverless_framework_multiple_functions():
    serverless_framework("tests/dev/multiple-functions.py")


def test_integration_serverless_framework_existing_function():
    project_id = serverless_framework("tests/dev/app.py", do_cleanup=False)
    serverless_framework("tests/dev/app.py", do_cleanup=True, project_id=project_id)


def test_integration_serverless_framework_multiple_existing_functions():
    project_id = serverless_framework(
        "tests/dev/multiple-functions.py", do_cleanup=False
    )
    serverless_framework(
        "tests/dev/multiple-functions.py", do_cleanup=True, project_id=project_id
    )


def test_integration_serverless_framework_one_existing_function():
    project_id = serverless_framework("tests/dev/app.py", do_cleanup=False)
    serverless_framework(
        "tests/dev/multiple-functions.py", do_cleanup=True, project_id=project_id
    )
