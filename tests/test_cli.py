import os.path

from click.testing import CliRunner

from scw_serverless.cli import cli


def init_runner(args: list):
    runner = CliRunner()
    return runner.invoke(cli, args)


def test_cli_generate_no_args():
    """
    Test the generate command with no args (other than the file selector)
    :return:
    """
    result = init_runner(["generate", "-f", "./dev/app.py"])
    assert result.exit_code == 0
    assert "Done" in result.output


def test_cli_generate_target_serverless():
    """
    Test the generate command targeting the serverless framework
    :return:
    """
    result = init_runner(["generate", "-f", "./dev/app.py", "-t", "serverless"])
    assert result.exit_code == 0
    assert "Done" in result.output
    assert "serverless" in result.output


def test_cli_generate_save_destination():
    """
    Test the generate command with a specific save folder path
    :return:
    """
    result = init_runner(["generate", "-f", "./dev/app.py", "-s", "./test"])
    assert result.exit_code == 0
    assert "Done" in result.output
    assert os.path.exists("./test/serverless.yml")


def test_cli_generate_no_args_multiple_functions():
    """
    Test the generate command with no args (other than the file selector)
    :return:
    """
    result = init_runner(["generate", "-f", "./dev/multiple-functions.py"])
    assert result.exit_code == 0
    assert "Done" in result.output


def test_cli_generate_target_serverless_multiple_functions():
    """
    Test the generate command targeting the serverless framework
    :return:
    """
    result = init_runner(
        ["generate", "-f", "./dev/multiple-functions.py", "-t", "serverless"]
    )
    assert result.exit_code == 0
    assert "Done" in result.output
    assert "serverless" in result.output


def test_cli_generate_save_destination_multiple_functions():
    """
    Test the generate command with a specific save folder path
    :return:
    """
    result = init_runner(
        ["generate", "-f", "./dev/multiple-functions.py", "-s", "./test"]
    )
    assert result.exit_code == 0
    assert "Done" in result.output
    assert os.path.exists("./test/serverless.yml")
