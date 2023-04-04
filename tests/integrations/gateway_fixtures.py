import boto3
import pytest
import requests

from tests import constants

from .utils import create_client


@pytest.fixture()
def auth_key() -> str:
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
