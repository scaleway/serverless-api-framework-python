# pylint: disable=unused-import,redefined-outer-name # fixture
from tests.integrations.utils import serverless_test_project  # noqa: F401
from tests.integrations.utils import ServerlessTestProject
from tests.utils import APP_PY_PATH


def test_integration_serverless_framework(
    serverless_test_project: ServerlessTestProject,  # noqa: F811
):
    serverless_test_project.generate_serverless_framework(APP_PY_PATH)


# Due to external factors these test will randomly fail.
# def test_integration_serverless_framework_multiple_functions():
#     serverless_framework(test_utils.MULTIPLE_FUNCTIONS_PY_PATH)
#
#
# def test_integration_serverless_framework_existing_function():
#     project_id = serverless_framework(test_utils.APP_PY_PATH, do_cleanup=False)
#    serverless_framework(test_utils.APP_PY_PATH, do_cleanup=True, project_id=project_id)
#
#
# def test_integration_serverless_framework_multiple_existing_functions():
#     project_id = serverless_framework(
#         test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=False
#     )
#     serverless_framework(
#         test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=True, project_id=project_id
#     )
#
#
# def test_integration_serverless_framework_one_existing_function():
#     project_id = serverless_framework(test_utils.APP_PY_PATH, do_cleanup=False)
#     serverless_framework(
#         test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=True, project_id=project_id
#     )
