import os
import random
import time
import typing as t

import pytest
from scaleway import Client
from scaleway.account.v2 import AccountV2API
from scaleway.function.v1beta1 import FunctionV1Beta1API
from scaleway.registry.v1 import RegistryV1API
from scaleway_core.api import ScalewayException
from scaleway_core.utils import WaitForOptions

from .utils import create_client

COMMIT_SHA = os.getenv("GITHUB_SHA", "local")

ProjectID = str


@pytest.fixture()
def scaleway_project() -> t.Iterator[ProjectID]:
    client = create_client()
    project_id = None
    try:
        project_id = _create_scaleway_project(client)
        yield project_id
    finally:
        if project_id:
            _cleanup_project(client, project_id)
            _delete_scaleway_project(client, project_id)


def _create_scaleway_project(client: Client) -> ProjectID:
    name = f"apifw-{COMMIT_SHA[:7]}-{random.randint(0, 9999)}"  # nosec # unsafe rng
    project = AccountV2API(client).create_project(
        name=name,
        description="Created by the Serverless API Framework integration suite.",
    )
    return project.id


def _cleanup_project(client: Client, project_id: ProjectID):
    """Delete all Scaleway resources created in the temporary project."""
    function_api = FunctionV1Beta1API(client)

    namespaces = function_api.list_namespaces_all(project_id=project_id)
    for namespace in namespaces:
        function_api.delete_namespace(namespace_id=namespace.id)

    registry_api = RegistryV1API(client)
    registries = registry_api.list_namespaces_all(project_id=project_id)
    for registry in registries:
        registry_api.delete_namespace(namespace_id=registry.id)

    # All deletions have been scheduled,
    # we can wait for their completion sequentially
    for namespace in namespaces:
        try:
            function_api.wait_for_namespace(namespace_id=namespace.id)
        except ScalewayException as e:
            if e.status_code != 404:
                raise e
    for registry in registries:
        try:
            registry_api.wait_for_namespace(namespace_id=registry.id, options=WaitForOptions(timeout=600))
        except ScalewayException as e:
            if e.status_code != 404:
                raise e


def _delete_scaleway_project(
    client: Client, project_id: ProjectID, max_tries: int = 10
):
    api = AccountV2API(client)
    for _ in range(max_tries):
        try:
            api.delete_project(project_id=project_id)
            return
        except ScalewayException as e:
            # This is just very finicky, the account API is somewhat unstable.
            print(e)
            time.sleep(10)
