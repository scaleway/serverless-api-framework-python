# pylint: disable=unused-import,redefined-outer-name # fixture
import requests

from tests import constants
from tests.app_fixtures.routed_functions import MESSAGES
from tests.integrations.deploy_wrapper import run_deploy_command
from tests.integrations.gateway_fixtures import auth_key  # noqa
from tests.integrations.project_fixture import scaleway_project  # noqa
from tests.integrations.utils import create_client


def test_integration_gateway(scaleway_project: str, auth_key: str):  # noqa
    client = create_client()
    client.default_project_id = scaleway_project

    gateway_url = f"https://{constants.GATEWAY_HOST}"

    run_deploy_command(
        client,
        constants.APP_FIXTURES_PATH / "routed_functions.py",
        "--gateway-url",
        gateway_url,
        "--gateway-api-key",
        auth_key,
    )

    # Check general routing configuration
    resp = requests.get(
        url=gateway_url + "/health", timeout=constants.COLD_START_TIMEOUT
    )
    assert resp.status_code == 200
    assert resp.text == MESSAGES["/health"]

    # Test with common prefix with configured routes
    resp = requests.get(
        url=gateway_url + "/messages", timeout=constants.COLD_START_TIMEOUT
    )
    assert resp.status_code == 200
    assert resp.text == MESSAGES["/messages"]

    # Check a route with a method that is not configured
    resp = requests.post(
        url=gateway_url + "/messages", timeout=constants.COLD_START_TIMEOUT
    )
    assert resp.status_code == 404

    resp = requests.post(
        url=gateway_url + "/messages/new",
        timeout=constants.COLD_START_TIMEOUT,
        data="welcome",
    )
    assert resp.status_code == 200
    assert "welcome" in resp.text

    resp = requests.put(
        url=gateway_url + "/messages/welcome",
        timeout=constants.COLD_START_TIMEOUT,
    )
    assert resp.status_code == 200
    assert "welcome" in resp.text
