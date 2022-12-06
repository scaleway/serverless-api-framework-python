import os.path

from click.testing import CliRunner

from scw_serverless.cli import cli
from tests.utils import APP_PY_PATH, TESTS_DIR


def _init_runner(args: list):
    runner = CliRunner()
    return runner.invoke(cli, args)


def test_cli_generate_no_args():
    """Test the generate command with no args"""
    result = _init_runner(["generate", APP_PY_PATH])
    assert result.exit_code == 0
    assert "Done" in result.output


def test_cli_generate_target_serverless():
    """Test the generate command targeting the serverless framework"""
    result = _init_runner(["generate", APP_PY_PATH, "-t", "serverless"])
    assert result.exit_code == 0
    assert "Done" in result.output
    assert "serverless" in result.output


def test_cli_generate_save_destination():
    """Test the generate command with a specific save folder path"""
    result = _init_runner(["generate", APP_PY_PATH, "-s", "./test"])
    assert result.exit_code == 0
    assert "Done" in result.output
    assert os.path.exists("./test/serverless.yml")


def test_cli_generate_no_args_multiple_functions():
    """Test the generate command with no args and multiple functions"""
    result = _init_runner(["generate", f"{TESTS_DIR}/dev/multiple_functions.py"])
    assert result.exit_code == 0
    assert "Done" in result.output


def test_cli_generate_target_serverless_multiple_functions():
    """Test the generate command targeting the serverless framework"""
    result = _init_runner(
        ["generate", f"{TESTS_DIR}/dev/multiple_functions.py", "-t", "serverless"]
    )
    assert result.exit_code == 0
    assert "Done" in result.output
    assert "serverless" in result.output


def test_cli_generate_save_destination_multiple_functions():
    """Test the generate command with a specific save folder path"""
    result = _init_runner(
        ["generate", f"{TESTS_DIR}/dev/multiple_functions.py", "-s", "./test"]
    )
    assert result.exit_code == 0
    assert "Done" in result.output
    assert os.path.exists("./test/serverless.yml")
