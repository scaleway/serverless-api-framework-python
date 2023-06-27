import requests
from click.testing import CliRunner

from tests import constants
from tests.app_fixtures import routed_functions
from tests.integrations import utils


def test_integration_gateway(cli_runner: CliRunner):
    messages = routed_functions.MESSAGES

    gateway_domain = utils.get_gateway_endpoint()
    gateway_url = "https://" + gateway_domain

    res = utils.run_deploy_command(
        cli_runner,
        app=routed_functions,
    )

    assert res.exit_code == 0, res.output

    # Check general routing configuration
    # Wait as the gateway is not immediately available
    resp = utils.wait_for_body_text(
        domain_name=gateway_domain + "/health", body=messages["/health"]
    )
    assert resp.status_code == 200

    # Test with common prefix with configured routes
    resp = requests.get(
        url=gateway_url + "/messages", timeout=constants.COLD_START_TIMEOUT
    )
    assert resp.status_code == 200
    assert resp.text == messages["/messages"]

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
