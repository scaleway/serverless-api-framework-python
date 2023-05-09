import logging
import os
import random
import time
import typing as t

import boto3
import pytest
import requests
from click.testing import CliRunner
from scaleway import Client
from scaleway.account.v2 import AccountV2API
from scaleway.function.v1beta1 import FunctionV1Beta1API
from scaleway_core.api import ScalewayException

from tests import constants

from .utils import create_client

COMMIT_SHA = os.getenv("GITHUB_SHA", "local")


@pytest.fixture()
def cli_runner(scaleway_project: str):  # pylint: disable=redefined-outer-name
    client = create_client()
    runner = CliRunner(
        env={
            "SCW_SECRET_KEY": client.secret_key,
            "SCW_ACCESS_KEY": client.access_key,
            "SCW_DEFAULT_PROJECT_ID": scaleway_project,
            "SCW_DEFAULT_REGION": client.default_region,
        }
    )
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture()
def scaleway_project() -> t.Iterator[str]:
    client = create_client()
    project_id = None
    try:
        project_id = _create_scaleway_project(client)
        yield project_id
    finally:
        if project_id:
            _cleanup_project(client, project_id)
            _delete_scaleway_project(client, project_id)


@pytest.fixture()
def gateway_auth_key() -> str:
    assert constants.GATEWAY_HOST, "Gateway needs to be configured."

    client = create_client()

    response = requests.post(
        "https://" + constants.GATEWAY_HOST + "/token",
        timeout=constants.COLD_START_TIMEOUT,
    )
    response.raise_for_status()

    s3 = boto3.resource(
        "s3",
        region_name=constants.GATEWAY_S3_BUCKET_NAME,
        endpoint_url=constants.GATEWAY_S3_BUCKET_ENDPOINT,
        aws_access_key_id=client.access_key,
        aws_secret_access_key=client.secret_key,
    )

    objects = sorted(
        s3.Bucket(constants.GATEWAY_S3_BUCKET_NAME).objects.all(),  # type: ignore
        key=lambda obj: obj.last_modified,
        reverse=True,
    )
    key = objects[0].key
    return key


def _create_scaleway_project(client: Client) -> str:
    name = f"apifw-{COMMIT_SHA[:7]}-{random.randint(0, 9999)}"  # nosec # unsafe rng
    logging.info("Creating project %s for integration tests", name)
    project = AccountV2API(client).create_project(
        name=name,
        description="Created by the Serverless API Framework integration suite.",
    )
    return project.id


def _cleanup_project(client: Client, project_id: str):
    """Delete all Scaleway resources created in the temporary project."""
    api = FunctionV1Beta1API(client)

    namespaces = api.list_namespaces_all(project_id=project_id)
    for namespace in namespaces:
        api.delete_namespace(namespace_id=namespace.id)

    # All deletions have been scheduled,
    # we can wait for their completion sequentially
    for namespace in namespaces:
        try:
            api.wait_for_namespace(namespace_id=namespace.id)
        except ScalewayException as e:
            if e.status_code != 404:
                raise e


def _delete_scaleway_project(client: Client, project_id: str, max_tries: int = 10):
    api = AccountV2API(client)
    logging.info("Deleting project %s for integration tests", project_id)
    for _ in range(max_tries):
        try:
            api.delete_project(project_id=project_id)
            return
        except ScalewayException as e:
            if e.status_code == 404:
                return
            logging.error(e, exc_info=True)
            time.sleep(10)
