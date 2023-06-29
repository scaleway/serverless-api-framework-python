from unittest.mock import MagicMock

import pytest
import responses
from responses.matchers import query_param_matcher
from scaleway import Client

from scw_serverless.app import Serverless
from scw_serverless.config import Function
from scw_serverless.config.route import GatewayRoute, HTTPMethod
from scw_serverless.gateway.gateway_manager import GatewayManager
from tests import constants

HELLO_WORLD_MOCK_DOMAIN = (
    "helloworldfunctionnawns8i8vo-hello-world.functions.fnc.fr-par.scw.cloud"
)


# pylint: disable=redefined-outer-name # fixture
@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture()
def app_gateway_manager() -> GatewayManager:
    app = Serverless("test-namespace")
    client = Client(
        access_key="SCWXXXXXXXXXXXXXXXXX",
        # The uuid is validated
        secret_key="498cce73-2a07-4e8c-b8ef-8f988e3c6929",  # nosec # false positive
        default_region=constants.DEFAULT_REGION,
    )
    return GatewayManager(app_instance=app, gateway=MagicMock(), sdk_client=client)


def test_gateway_manager_update_routes(
    app_gateway_manager: GatewayManager, mocked_responses: responses.RequestsMock
):
    gateway_route = GatewayRoute(relative_url="/hello", http_methods=[HTTPMethod.GET])
    function = Function(
        name="test-function",
        handler_path="handler",
        gateway_route=gateway_route,
    )
    app_gateway_manager.app_instance.functions = [function]

    namespace = {
        "id": "namespace-id",
        "name": app_gateway_manager.app_instance.service_name,
        "secret_environment_variables": [],  # Otherwise breaks the marshalling
    }
    # Looking for existing namespace
    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/namespaces",
        json={"namespaces": [namespace]},
    )
    # We have to provide a stop gap otherwise list_namepaces_all() will keep
    # making API calls.
    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/namespaces",
        json={"namespaces": []},
    )

    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/functions",
        match=[query_param_matcher({"namespace_id": namespace["id"], "page": 1})],
        json={
            "functions": [
                {
                    "name": function.name,
                    "domain_name": HELLO_WORLD_MOCK_DOMAIN,
                    "secret_environment_variables": [],
                }
            ]
        },
    )
    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/functions",
        match=[query_param_matcher({"namespace_id": namespace["id"], "page": 2})],
        json={"functions": []},
    )

    app_gateway_manager.update_routes()

    # Update the route with the domain name
    gateway_route.target = HELLO_WORLD_MOCK_DOMAIN

    gateway_mock = app_gateway_manager.gateway
    gateway_mock.add_route.assert_called_once_with(
        gateway_route,
    )
