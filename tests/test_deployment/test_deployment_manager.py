from typing import Any
from unittest.mock import MagicMock

import pytest
import responses
import scaleway.function.v1beta1 as sdk
from responses import matchers
from scaleway import Client

from scw_serverless.app import Serverless
from scw_serverless.config import Function
from scw_serverless.config.triggers import CronTrigger
from scw_serverless.deployment import DeploymentManager
from tests import constants

RUNTIME = sdk.FunctionRuntime.PYTHON311


# pylint: disable=redefined-outer-name # fixture
@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture(autouse=True)
def mocked_pool_starmap(monkeypatch: Any):
    """Provides a simple starmap implementation which does not rely on pickling."""
    monkeypatch.setattr(
        "multiprocessing.pool.Pool.starmap",
        lambda self, func, args: [func(*arg) for arg in args],
    )


def get_test_backend() -> DeploymentManager:
    app = Serverless("test-namespace")
    client = Client(
        access_key="SCWXXXXXXXXXXXXXXXXX",
        # The uuid is validated
        secret_key="498cce73-2a07-4e8c-b8ef-8f988e3c6929",  # nosec # fake data
        default_region=constants.DEFAULT_REGION,
    )
    backend = DeploymentManager(app, client, False, runtime=RUNTIME)
    # This would otherwise create some side effects
    create_zip = MagicMock()
    create_zip.return_value = 300
    backend._create_deployment_zip = create_zip
    # This is mocked because it reads the zip
    backend._upload_deployment_zip = MagicMock()
    return backend


def test_scaleway_api_backend_deploy_function(mocked_responses: responses.RequestsMock):
    function = Function(
        name="test-function",
        handler="handler",
    )
    backend = get_test_backend()
    backend.app_instance.functions = [function]

    # Looking for existing namespace
    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/namespaces",
        json={"namespaces": []},
    )
    namespace = {
        "id": "namespace-id",
        "name": backend.app_instance.service_name,
        "secret_environment_variables": [],  # Otherwise breaks the marshalling
    }
    # Creating namespace
    mocked_responses.post(
        constants.SCALEWAY_FNC_API_URL + "/namespaces", json=namespace
    )
    # Polling its status
    mocked_responses.get(
        f'{ constants.SCALEWAY_FNC_API_URL}/namespaces/{namespace["id"]}',
        json=namespace | {"status": sdk.NamespaceStatus.READY},
    )
    # Looking for existing function
    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/functions",
        match=[
            matchers.query_param_matcher(
                {"namespace_id": namespace["id"], "page": 1, "name": function.name}
            ),
        ],
        json={"functions": []},
    )
    # Creating a function
    mocked_fn = {
        "id": "function-id",
        "name": function.name,
        "secret_environment_variables": [],
    }
    mocked_responses.post(
        constants.SCALEWAY_FNC_API_URL + "/functions",
        match=[
            matchers.json_params_matcher(
                {
                    "name": function.name,
                    "privacy": sdk.FunctionPrivacy.PUBLIC,
                    "http_option": sdk.FunctionHttpOption.REDIRECTED,
                    "handler": "handler",
                    "runtime": sdk.FunctionRuntime.PYTHON311,
                },
                # Ignore None values which will be dropped by the marshalling
                strict_match=False,
            )
        ],
        json=mocked_fn,
    )
    test_fn_api_url = f'{constants.SCALEWAY_FNC_API_URL}/functions/{mocked_fn["id"]}'
    mocked_responses.get(
        test_fn_api_url + "/upload-url",
        json={"url": "https://url"},
    )
    mocked_responses.post(
        test_fn_api_url + "/deploy",
        json=mocked_fn,
    )
    # Poll the status
    mocked_responses.get(
        test_fn_api_url,
        json=mocked_fn | {"status": sdk.FunctionStatus.PENDING},
    )
    mocked_responses.get(
        test_fn_api_url,
        json=mocked_fn | {"status": sdk.FunctionStatus.READY},
    )
    backend.deploy()


def test_scaleway_api_backend_deploy_function_with_trigger(
    mocked_responses: responses.RequestsMock,
):
    trigger = CronTrigger(schedule="* * * * * *", name="test-cron", args={"foo": "bar"})
    function = Function(
        name="test-function-with-trigger",
        handler="handler",
        triggers=[trigger],
    )

    backend = get_test_backend()
    backend.app_instance.functions = [function]

    # Looking for existing namespace
    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/namespaces",
        json={"namespaces": []},
    )
    namespace = {
        "id": "namespace-id",
        "name": backend.app_instance.service_name,
        "secret_environment_variables": [],  # Otherwise breaks the marshalling
    }
    # Creating namespace
    mocked_responses.post(
        constants.SCALEWAY_FNC_API_URL + "/namespaces", json=namespace
    )
    # Polling its status
    mocked_responses.get(
        f'{ constants.SCALEWAY_FNC_API_URL}/namespaces/{namespace["id"]}',
        json=namespace | {"status": sdk.NamespaceStatus.READY},
    )
    # Looking for existing function
    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/functions",
        match=[
            matchers.query_param_matcher(
                {"namespace_id": namespace["id"], "page": 1, "name": function.name}
            ),
        ],
        json={"functions": []},
    )
    # Creating a function
    mocked_fn = {
        "id": "function-id",
        "name": function.name,
        "secret_environment_variables": [],
    }
    mocked_responses.post(
        constants.SCALEWAY_FNC_API_URL + "/functions",
        match=[
            matchers.json_params_matcher(
                {
                    "name": function.name,
                    "privacy": sdk.FunctionPrivacy.PUBLIC,
                    "http_option": sdk.FunctionHttpOption.REDIRECTED,
                    "handler": "handler",
                    "runtime": RUNTIME,
                },
                # Ignore None values which will be dropped by the marshalling
                strict_match=False,
            )
        ],
        json=mocked_fn,
    )
    test_fn_api_url = f'{ constants.SCALEWAY_FNC_API_URL}/functions/{mocked_fn["id"]}'
    mocked_responses.get(
        test_fn_api_url + "/upload-url",
        json={"url": "https://url"},
    )
    mocked_responses.post(
        test_fn_api_url + "/deploy",
        json=mocked_fn,
    )
    # Poll the status
    mocked_responses.get(
        test_fn_api_url,
        json=mocked_fn | {"status": sdk.FunctionStatus.READY},
    )
    # Looking for existing cron
    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/crons",
        match=[
            matchers.query_param_matcher({"function_id": mocked_fn["id"], "page": 1})
        ],
        json={"crons": []},
    )
    cron = {"id": "cron-id"}
    mocked_responses.post(
        constants.SCALEWAY_FNC_API_URL + "/crons",
        match=[
            matchers.json_params_matcher(
                {
                    "function_id": mocked_fn["id"],
                    "name": trigger.name,
                    "schedule": trigger.schedule,
                    "args": trigger.args,
                }
            )
        ],
        json=cron,
    )
    # Poll the status
    mocked_responses.get(
        f'{ constants.SCALEWAY_FNC_API_URL}/crons/{cron["id"]}',
        json=mocked_fn | {"status": sdk.CronStatus.READY},
    )
    backend.deploy()
