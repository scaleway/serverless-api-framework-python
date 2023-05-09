import scaleway.function.v1beta1 as sdk
from click.testing import CliRunner

from tests.app_fixtures import app, app_updated, cron_app, multiple_functions
from tests.integrations import utils


def test_deploy(scaleway_project: str, cli_runner: CliRunner):
    runtime = "python310"
    res = utils.run_deploy_command(cli_runner, app=app, args=["--runtime", runtime])

    assert res.exit_code == 0, res.output

    client = utils.create_client(project_id=scaleway_project)
    functions = utils.get_deployed_functions_by_name(client, app.app)
    deployed_function = functions["hello-world"]

    resp = utils.trigger_function(deployed_function.domain_name)
    # Check function response
    assert resp.text == app.MESSAGE

    # Check function configuration
    function = app.app.functions[0]
    assert deployed_function.memory_limit == function.memory_limit
    assert deployed_function.privacy == function.privacy
    assert deployed_function.runtime == runtime
    assert deployed_function.environment_variables == function.environment_variables


def test_deploy_existing_function(scaleway_project: str, cli_runner: CliRunner):
    res = utils.run_deploy_command(cli_runner=cli_runner, app=app)

    assert res.exit_code == 0, res.output

    client = utils.create_client(project_id=scaleway_project)
    functions = utils.get_deployed_functions_by_name(client, app.app)
    function = functions["hello-world"]

    resp = utils.trigger_function(function.domain_name)
    # Check message content
    assert resp.text == app.MESSAGE
    assert function.description == app.DESCRIPTION

    # Deploy twice in a row
    res = utils.run_deploy_command(cli_runner=cli_runner, app=app_updated)

    functions = utils.get_deployed_functions_by_name(client, app_updated.app)
    function = functions["hello-world"]

    # Check updated message content
    utils.wait_for_body_text(function.domain_name, app_updated.MESSAGE)

    assert function.description == app_updated.DESCRIPTION


def test_deploy_multiple_functions(scaleway_project: str, cli_runner: CliRunner):
    res = utils.run_deploy_command(cli_runner=cli_runner, app=multiple_functions)

    assert res.exit_code == 0, res.output

    client = utils.create_client(project_id=scaleway_project)
    functions = utils.get_deployed_functions_by_name(client, multiple_functions.app)

    for function_name, message in multiple_functions.MESSAGES.items():
        resp = utils.trigger_function(functions[function_name].domain_name)
        assert resp.text == message


def test_deploy_function_with_cron(scaleway_project: str, cli_runner: CliRunner):
    res = utils.run_deploy_command(cli_runner=cli_runner, app=cron_app)

    assert res.exit_code == 0

    client = utils.create_client(project_id=scaleway_project)
    functions = utils.get_deployed_functions_by_name(client, cron_app.app)
    deployed_function = functions["hello-world-cron"]

    resp = utils.trigger_function(deployed_function.domain_name)
    # Check function reponse
    assert resp.status_code == 200

    # Check that a Cron was created
    function = cron_app.app.functions[0]
    api = sdk.FunctionV1Beta1API(client)
    crons = api.list_crons_all(function_id=deployed_function.id)

    assert crons
    deployed_cron = crons[0]
    cron = function.triggers[0]
    assert deployed_cron.name == cron.name
    assert deployed_cron.args == cron.args
