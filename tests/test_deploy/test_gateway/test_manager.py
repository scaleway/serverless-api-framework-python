# from unittest.mock import MagicMock

# import pytest

# from scw_serverless.deploy import gateway
# from scw_serverless.deploy.gateway.models import GatewayInput, GatewayOutput, Route
# from scw_serverless.utils.http import HTTPMethod

# from ...dev.gateway import app

# MOCK_UUID = "xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx"
# HELLO_WORLD_MOCK_ENDPOINT = (
#     "https://helloworldfunctionnawns8i8vo-hello-world.functions.fnc.fr-par.scw.cloud"
# )
# PROJECT_ID = "projecti-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx"


# @pytest.fixture
# def app_gateway_manager():
#     api, gateway_client = MagicMock(), MagicMock()
#     gateway_uuid = MOCK_UUID
#     return gateway.GatewayManager(app, api, "", gateway_uuid, gateway_client)


# def test_gateway_manager_get_routes(app_gateway_manager):
#     routes = app_gateway_manager._get_routes(
#         {"hello-world": {"domain_name": HELLO_WORLD_MOCK_ENDPOINT}}
#     )

#     assert len(routes) == 1
#     assert (
#         Route(path="/", target=HELLO_WORLD_MOCK_ENDPOINT, methods=[HTTPMethod.GET])
#         in routes
#     )


# def test_gateway_manager_update_gateway_routes_with_gw_id(app_gateway_manager):
#     api: MagicMock = app_gateway_manager.api
#     client: MagicMock = app_gateway_manager.gateway_client

#     api.list_functions.return_value = [
#         {"name": "hello-world", "domain_name": HELLO_WORLD_MOCK_ENDPOINT}
#     ]
#     client.get_gateway.return_value = GatewayOutput(MOCK_UUID, ["toto.fr"], [])

#     app_gateway_manager.update_gateway_routes()

#     client.get_gateway.assert_called_once_with(MOCK_UUID)
#     client.update_gateway.assert_called_once_with(
#         MOCK_UUID,
#         GatewayInput(
#             ["example.org", "toto.fr"],
#             [
#                 Route(
#                     path="/", target=HELLO_WORLD_MOCK_ENDPOINT, methods=[HTTPMethod.GET]
#                 )
#             ],
#         ),
#     )


# def test_gateway_manager_update_gateway_routes_without_gw_id(app_gateway_manager):
#     app_gateway_manager.gateway_uuid = None  # Set the gateway_uuid to None

#     api: MagicMock = app_gateway_manager.api
#     client: MagicMock = app_gateway_manager.gateway_client

#     api.list_functions.return_value = [
#         {"name": "hello-world", "domain_name": HELLO_WORLD_MOCK_ENDPOINT}
#     ]
#     app_gateway_manager.update_gateway_routes()

#     client.create_gateway.assert_called_once_with(
#         GatewayInput(
#             ["example.org"],
#             [
#                 Route(
#                     path="/", target=HELLO_WORLD_MOCK_ENDPOINT, methods=[HTTPMethod.GET]
#                 )
#             ],
#         ),
#     )
