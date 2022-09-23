import tests.utils as test_utils
from tests.integrations.utils import deploy


def test_integration_deploy_using_srvless_fw():
    deploy(test_utils.APP_PY_PATH, backend="serverless")


def test_integration_deploy_multiple_functions_using_srvless_fw():
    deploy(test_utils.MULTIPLE_FUNCTIONS_PY_PATH, backend="serverless")


def test_integration_deploy_existing_function_using_srvless_fw():
    project_id = deploy(test_utils.APP_PY_PATH, do_cleanup=False, backend="serverless")
    deploy(
        test_utils.APP_PY_PATH,
        do_cleanup=True,
        project_id=project_id,
        backend="serverless",
    )


def test_integration_deploy_multiple_existing_functions_using_srvless_fw():
    project_id = deploy(
        test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=False, backend="serverless"
    )
    deploy(
        test_utils.MULTIPLE_FUNCTIONS_PY_PATH,
        do_cleanup=True,
        project_id=project_id,
        backend="serverless",
    )


def test_integration_deploy_one_existing_function_using_srvless_fw():
    project_id = deploy(test_utils.APP_PY_PATH, do_cleanup=False, backend="serverless")
    deploy(
        test_utils.MULTIPLE_FUNCTIONS_PY_PATH,
        do_cleanup=True,
        project_id=project_id,
        backend="serverless",
    )
