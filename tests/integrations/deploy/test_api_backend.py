import tests.utils as test_utils
from tests.integrations.utils import deploy


def test_integration_deploy():
    deploy(test_utils.APP_PY_PATH)


# Due to external factors these test will randomly fail.
# def test_integration_deploy_multiple_functions():
#     deploy(test_utils.MULTIPLE_FUNCTIONS_PY_PATH)
#
#
# def test_integration_deploy_existing_function():
#     project_id = deploy(test_utils.APP_PY_PATH, do_cleanup=False)
#     deploy(test_utils.APP_PY_PATH, do_cleanup=True, project_id=project_id)
#
#
# def test_integration_deploy_multiple_existing_functions():
#     project_id = deploy(test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=False)
#     deploy(
#         test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=True, project_id=project_id
#     )
#
#
# def test_integration_deploy_one_existing_function():
#     project_id = deploy(test_utils.APP_PY_PATH, do_cleanup=False)
#     deploy(
#         test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=True, project_id=project_id
#     )
