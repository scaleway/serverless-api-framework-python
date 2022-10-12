from scw_serverless.utils.commands import get_command_path
from scw_serverless.utils.string import module_to_path
from tests.dev.app import app
from tests.dev.multiple_functions import app as multiple_app


def test_module_to_path():
    assert module_to_path("abc.def") == "abc/def"


def test_function_export():
    """
    Test if annotation are correctly exported and stored in the functions list.
    This test use the file dev/app.py
    :return:
    """
    assert len(app.functions) == 1


def test_multiple_function_export():
    assert len(multiple_app.functions) == 3


def test_get_command_path():
    assert get_command_path("serverless")
    assert get_command_path("node")
