from tests.app_fixtures.app import app
from tests.app_fixtures.multiple_functions import app as multiple_app


def test_function_export():
    """
    Test if annotation are correctly exported and stored in the functions list.
    This test use the file app_fixtures/app.py
    """
    assert len(app.functions) == 1


def test_multiple_function_export():
    assert len(multiple_app.functions) == 3
