# pylint: disable=unused-import,redefined-outer-name # fixture

import scaleway.function.v1beta1 as sdk

from tests import constants
from tests.app_fixtures import app, app_updated
from tests.integrations.deploy.deploy_wrapper import run_deploy_command
from tests.integrations.project_fixture import scaleway_project  # noqa
from tests.integrations.utils import create_client, trigger_function


def test_integration_deploy_serverless_backend(scaleway_project: str):  # noqa
    client = create_client()
    client.default_project_id = scaleway_project

    url, *_ = run_deploy_command(
        client, app_path=constants.APP_PY_PATH, backend="serverless"
    )

    # Check message content
    resp = trigger_function(url)
    assert resp.text == app.MESSAGE


def test_integration_deploy_existing_function_serverless_backend(
    scaleway_project: str,  # noqa
):
    client = create_client()
    client.default_project_id = scaleway_project

    url, *_ = run_deploy_command(
        client, app_path=constants.APP_PY_PATH, backend="serverless"
    )

    # Check message content
    resp = trigger_function(url)
    assert resp.text == app.MESSAGE

    # Get function_id
    api = sdk.FunctionV1Beta1API(client)
    namespace, *_ = api.list_namespaces_all(name=app.NAMESPACE_NAME)

    # Check description
    function, *_ = api.list_functions_all(namespace_id=namespace.id, name="hello-world")
    assert function.description == app.DESCRIPTION

    # Deploy twice in a row
    url, *_ = run_deploy_command(
        client,
        app_path=constants.APP_FIXTURES_PATH.joinpath("app_updated.py"),
    )

    # Check updated message content
    resp = trigger_function(url)
    assert resp.text == app_updated.MESSAGE

    # Check updated description
    function = api.get_function(function_id=function.id)
    assert function.description == app_updated.DESCRIPTION
