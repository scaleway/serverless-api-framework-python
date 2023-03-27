# pylint: disable=unused-import,redefined-outer-name # fixture

import time

import scaleway.function.v1beta1 as sdk

from tests import constants
from tests.app_fixtures import app, app_updated, multiple_functions
from tests.integrations.deploy_wrapper import run_deploy_command
from tests.integrations.project_fixture import scaleway_project  # noqa
from tests.integrations.utils import create_client, trigger_function


def test_integration_deploy(scaleway_project: str):  # noqa
    client = create_client()
    client.default_project_id = scaleway_project

    url, *_ = run_deploy_command(
        client,
        app_path=constants.APP_PY_PATH,
    )

    # Check message content
    resp = trigger_function(url)
    assert resp.text == app.MESSAGE


def test_integration_deploy_existing_function(scaleway_project: str):  # noqa
    client = create_client()
    client.default_project_id = scaleway_project

    url, *_ = run_deploy_command(
        client,
        app_path=constants.APP_PY_PATH,
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
        app_path=constants.APP_FIXTURES_PATH / "app_updated.py",
    )

    # TODO?: delete this
    time.sleep(30)

    # Check updated message content
    resp = trigger_function(url)
    assert resp.text == app_updated.MESSAGE

    # Check updated description
    function = api.get_function(function_id=function.id)
    assert function.description == app_updated.DESCRIPTION


def test_integration_deploy_multiple_functions(scaleway_project: str):  # noqa
    client = create_client()
    client.default_project_id = scaleway_project

    urls = run_deploy_command(
        client,
        app_path=constants.MULTIPLE_FUNCTIONS,
    )

    for url in urls:
        # Get the function_name from the url
        function_name = None
        for name in multiple_functions.MESSAGES:
            if name in url:
                function_name = name
        assert function_name

        resp = trigger_function(url)
        assert resp.text == multiple_functions.MESSAGES[function_name]
