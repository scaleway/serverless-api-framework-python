import tests.utils as test_utils
from tests.integrations.utils import terraform


def test_integration_terraform():
    terraform(test_utils.APP_PY_PATH)


def test_integration_terraform_multiple_functions():
    terraform(test_utils.MULTIPLE_FUNCTIONS_PY_PATH)


def test_integration_terraform_existing_function():
    project_id = terraform(test_utils.APP_PY_PATH, do_cleanup=False)
    terraform(test_utils.APP_PY_PATH, do_cleanup=True, project_id=project_id)


def test_integration_terraform_multiple_existing_functions():
    project_id = terraform(test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=False)
    terraform(
        test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=True, project_id=project_id
    )


def test_integration_terraform_one_existing_function():
    project_id = terraform(test_utils.APP_PY_PATH, do_cleanup=False)
    terraform(
        test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=True, project_id=project_id
    )
