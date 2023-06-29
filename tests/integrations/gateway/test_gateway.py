from click.testing import CliRunner

from tests import constants
from tests.app_fixtures import routed_functions
from tests.integrations import utils


def test_integration_gateway(cli_runner: CliRunner):
    messages = routed_functions.MESSAGES

    gateway_url = "https://" + utils.get_gateway_endpoint()

    res = utils.run_deploy_command(
        cli_runner,
        app=routed_functions,
    )
    assert res.exit_code == 0, res.output

    # Wait as the gateway is not immediately available
    session = utils.get_retry_session()

    # Check general routing configuration
    resp = session.get(gateway_url + "/health", timeout=constants.COLD_START_TIMEOUT)
    assert resp.status_code == 200
    assert resp.text == messages["/health"]

    # Test with common prefix with configured routes
    resp = session.get(
        url=gateway_url + "/messages", timeout=constants.COLD_START_TIMEOUT
    )
    assert resp.status_code == 200
    assert resp.text == messages["/messages"]

    # Check a route with a method that is not configured
    resp = session.post(
        url=gateway_url + "/messages", timeout=constants.COLD_START_TIMEOUT
    )
    assert resp.status_code == 404

    resp = session.post(
        url=gateway_url + "/messages/new",
        timeout=constants.COLD_START_TIMEOUT,
        data="welcome",
    )
    assert resp.status_code == 200
    assert "welcome" in resp.text

    # Check that the routes are not greedy
    # eg: /messages/new should not match /messages
    resp = session.put(
        url=gateway_url + "/messages/welcome",
        timeout=constants.COLD_START_TIMEOUT,
    )
    assert resp.status_code == 200
    assert "welcome" in resp.text
