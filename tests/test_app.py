from dev.app import app
from serverless.app import Serverless


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
