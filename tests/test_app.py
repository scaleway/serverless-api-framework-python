from scw_serverless.app import Serverless
from scw_serverless.utils.commands import get_command_path
from tests.dev.app import app


def test_module_to_path():
    serverless = Serverless("unit_test")
    assert serverless.module_to_path("abc.def") == "abc/def"


def test_function_export():
    """
    Test if annotation are correctly exported and stored in the functions list.
    This test use the file dev/app.py
    :return:
    """
    assert len(app.functions) == 1


def test_get_command_path():
    assert get_command_path("serverless")
    assert get_command_path("node")
