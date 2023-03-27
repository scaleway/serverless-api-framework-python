import typing as t

import boto3
import pytest
import requests
import scaleway.container.v1beta1 as sdk
from scaleway import Client

from tests import constants

from .utils import create_client


@pytest.fixture()
def api_gateway(scaleway_project: str) -> t.Iterator[sdk.Container]:
    client = create_client()
    container = None
    try:
        container = _deploy_gateway(scaleway_project, client)
        yield container
    finally:
        if container:
            _cleanup_gateway(client, container)


@pytest.fixture()
def auth_key(
    api_gateway: sdk.Container,  # pylint: disable=redefined-outer-name
) -> str:
    client = create_client()

    response = requests.post(
        "https://" + api_gateway.domain_name + "/token",
        timeout=constants.COLD_START_TIMEOUT,
    )
    response.raise_for_status()

    s3 = boto3.resource(
        "s3",
        region_name=constants.API_GATEWAY_S3_BUCKET,
        endpoint_url=constants.API_GATEWAY_S3_BUCKET_ENDPOINT,
        aws_access_key_id=client.access_key,
        aws_secret_access_key=client.secret_key,
    )

    objects = sorted(
        s3.Bucket(constants.API_GATEWAY_S3_BUCKET).objects.all(),  # type: ignore
        key=lambda obj: obj.last_modified,
        reverse=True,
    )
    key = objects[0].key
    return key


def _deploy_gateway(project_id: str, client: Client) -> sdk.Container:
    assert (
        constants.API_GATEWAY_S3_BUCKET
    ), "S3 bucket needs to be configured to deploy Gateway"

    api = sdk.ContainerV1Beta1API(client)
    namespace = api.create_namespace(name="gateway", project_id=project_id)
    api.wait_for_namespace(namespace_id=namespace.id)

    container = api.create_container(
        namespace_id=namespace.id,
        min_scale=1,
        max_scale=1,
        protocol=sdk.ContainerProtocol.HTTP1,
        registry_image=constants.API_GATEWAY_IMAGE,
        privacy=sdk.ContainerPrivacy.PUBLIC,
        http_option=sdk.ContainerHttpOption.REDIRECTED,
        memory_limit=constants.API_GATEWAY_MEMORY_LIMIT,
        secret_environment_variables=[
            sdk.Secret("SCW_ACCESS_KEY", client.access_key),
            sdk.Secret("SCW_SECRET_KEY", client.secret_key),
        ],
        environment_variables={
            "S3_REGION": constants.API_GATEWAY_S3_REGION,
            "S3_ENDPOINT": constants.API_GATEWAY_S3_BUCKET_ENDPOINT,
            "S3_BUCKET_NAME": constants.API_GATEWAY_S3_BUCKET,
        },
    )
    api.deploy_container(container_id=container.id)
    container = api.wait_for_container(container_id=container.id)

    return container


def _cleanup_gateway(client: Client, container: sdk.Container):
    """Delete all Scaleway resources created in the temporary project."""
    api = sdk.ContainerV1Beta1API(client)
    api.delete_container(container_id=container.id)
    api.delete_namespace(namespace_id=container.namespace_id)
