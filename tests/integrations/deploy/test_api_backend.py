# pylint: disable=unused-import,redefined-outer-name # fixture
from tests.integrations.utils import serverless_test_project  # noqa: F401
from tests.integrations.utils import ServerlessTestProject
from tests.utils import APP_PY_PATH


def test_integration_deploy(
    serverless_test_project: ServerlessTestProject,  # noqa: F811
):
    serverless_test_project.deploy(APP_PY_PATH, backend="api")


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
