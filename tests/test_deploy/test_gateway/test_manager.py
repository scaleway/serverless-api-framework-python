from unittest.mock import MagicMock

import pytest

from scw_serverless.config.route import HTTPMethod
from scw_serverless.deploy import gateway
from scw_serverless.deploy.gateway.models import GatewayInput, GatewayOutput, Route
from tests.dev.gateway import app

MOCK_UUID = "xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx"
HELLO_WORLD_MOCK_ENDPOINT = (
    "https://helloworldfunctionnawns8i8vo-hello-world.functions.fnc.fr-par.scw.cloud"
)
PROJECT_ID = "projecti-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx"


@pytest.fixture(name="app_gateway_manager")
def _app_gateway_manager() -> gateway.GatewayManager:
    mock_client, gateway_client = MagicMock(), MagicMock()
    gateway_uuid = MOCK_UUID
    manager = gateway.GatewayManager(app, mock_client, gateway_uuid, gateway_client)
    manager.api = mock_client
    return manager


def test_gateway_manager_get_routes(app_gateway_manager: gateway.GatewayManager):
    function = MagicMock()
    function.domain_name = HELLO_WORLD_MOCK_ENDPOINT
    routes = app_gateway_manager._get_routes({"hello-world": function})

    assert len(routes) == 1
    assert (
        Route(path="/", target=HELLO_WORLD_MOCK_ENDPOINT, methods=[str(HTTPMethod.GET)])
        in routes
    )


def test_gateway_manager_update_gateway_routes_with_gw_id(
    app_gateway_manager: gateway.GatewayManager,
):
    api: MagicMock = app_gateway_manager.api  # type: ignore
    client: MagicMock = app_gateway_manager.gateway_client  # type: ignore

    function = MagicMock()
    function.name = "hello-world"
    function.domain_name = HELLO_WORLD_MOCK_ENDPOINT
    api.list_functions_all.return_value = [function]
    client.get_gateway.return_value = GatewayOutput(MOCK_UUID, ["toto.fr"], [])

    app_gateway_manager.update_gateway_routes()

    client.get_gateway.assert_called_once_with(MOCK_UUID)
    client.update_gateway.assert_called_once_with(
        MOCK_UUID,
        GatewayInput(
            ["example.org", "toto.fr"],
            [
                Route(
                    path="/",
                    target=HELLO_WORLD_MOCK_ENDPOINT,
                    methods=[str(HTTPMethod.GET)],
                )
            ],
        ),
    )


def test_gateway_manager_update_gateway_routes_without_gw_id(
    app_gateway_manager: gateway.GatewayManager,
):
    app_gateway_manager.gateway_uuid = None  # Set the gateway_uuid to None

    api: MagicMock = app_gateway_manager.api  # type: ignore
    client: MagicMock = app_gateway_manager.gateway_client  # type: ignore

    function = MagicMock()
    function.name = "hello-world"
    function.domain_name = HELLO_WORLD_MOCK_ENDPOINT
    api.list_functions_all.return_value = [function]
    app_gateway_manager.update_gateway_routes()

    client.create_gateway.assert_called_once_with(
        GatewayInput(
            ["example.org"],
            [
                Route(
                    path="/",
                    target=HELLO_WORLD_MOCK_ENDPOINT,
                    methods=[str(HTTPMethod.GET)],
                )
            ],
        ),
    )
