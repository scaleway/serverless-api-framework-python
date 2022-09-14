import os
import subprocess

import requests


def create_project():
    sha = os.getenv("GITHUB_SHA")
    if sha is None:
        sha = "local"
    req = requests.post(
        "https://api.scaleway.com/account/v2/projects",
        json={"name": f"apifw-{sha}", "organization_id": os.getenv("SCW_ORG_ID")},
        headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
    )

    req.raise_for_status()

    return req.json()["id"]


def delete_project(project_id):
    req = requests.delete(
        f"https://api.scaleway.com/account/v2/projects/{project_id}",
        headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
    )
    req.raise_for_status()


def test_integration_serverless_framework():
    project_id = create_project()

    # TODO: Run the command line

    ret = subprocess.run(
        [
            "../venv/bin/srvlss",
            "generate",
            "-t",
            "serverless",
            "-f",
            "./dev/app.py",
            "-s",
            "./test",
        ],
        env={
            "SCW_SECRET_KEY": os.getenv("SCW_SECRET_KEY"),
            "SCW_DEFAULT_PROJECT_ID": project_id,
            "SCW_REGION": "fr-par",
        },
        # shell=True,
    )

    assert ret.returncode == 0
    # TODO: Run the serverless Framework

    delete_project(project_id)
