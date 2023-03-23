import pytest
import responses
import scaleway.function.v1beta1 as sdk
from scaleway import Client

from scw_serverless.app import Serverless
from scw_serverless.config import Function
from scw_serverless.config.route import GatewayRoute, HTTPMethod
from scw_serverless.gateway.gateway_manager import GatewayManager
from tests import constants

HELLO_WORLD_MOCK_DOMAIN = (
    "helloworldfunctionnawns8i8vo-hello-world.functions.fnc.fr-par.scw.cloud"
)
MOCK_GATEWAY_URL = "https://my-gateway-domain.com"
MOCK_GATEWAY_API_KEY = "7tfxBRB^vJbBcR5s#*RE"
MOCK_UUID = "xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx"
PROJECT_ID = "projecti-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx"


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
        secret_key="498cce73-2a07-4e8c-b8ef-8f988e3c6929",
        default_region=constants.DEFAULT_REGION,
    )
    return GatewayManager(app, MOCK_GATEWAY_URL, MOCK_GATEWAY_API_KEY, client)


def test_gateway_manager_update_routes(
    app_gateway_manager: GatewayManager, mocked_responses: responses.RequestsMock
):
    function = Function(
        name="test-function",
        handler="handler",
        runtime=sdk.FunctionRuntime.PYTHON311,
        gateway_route=GatewayRoute(
            relative_url="/hello", http_methods=[HTTPMethod.GET]
        ),
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

    mocked_responses.get(
        constants.SCALEWAY_FNC_API_URL + "/functions",
        match=[
            responses.matchers.query_param_matcher(
                {"namespace_id": namespace["id"], "page": 1}
            )
        ],
        json={"functions": []},
    )

    app_gateway_manager.update_routes()
