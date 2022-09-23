from dev.app import app

from scw_serverless.utils import module_to_path


def test_module_to_path():
    assert module_to_path("abc.def") == "abc/def"


def test_function_export():
    """
    Test if annotation are correctly exported and stored in the functions list.
    This test use the file dev/app.py
    :return:
    """
    assert len(app.functions) == 1
