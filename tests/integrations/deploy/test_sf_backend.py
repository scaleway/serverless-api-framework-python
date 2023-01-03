from typing import Tuple

import tests.utils as test_utils

# pylint: disable=unused-import # fixture
from tests.integrations.utils import _create_serverless_project, deploy  # noqa: F401


def test_integration_deploy_using_srvless_fw(serverless_project: Tuple[str, str]):
    deploy(
        test_utils.APP_PY_PATH,
        serverless_project=serverless_project,
        backend="serverless",
    )


# Due to external factors these test will randomly fail.
# def test_integration_deploy_multiple_functions_using_srvless_fw():
#     deploy(test_utils.MULTIPLE_FUNCTIONS_PY_PATH, backend="serverless")
#
#
# def test_integration_deploy_existing_function_using_srvless_fw():
#     project_id = deploy(test_utils.APP_PY_PATH, do_cleanup=False, backend="serverless")
#     deploy(
#         test_utils.APP_PY_PATH,
#         do_cleanup=True,
#         project_id=project_id,
#         backend="serverless",
#     )
#
#
# def test_integration_deploy_multiple_existing_functions_using_srvless_fw():
#     project_id = deploy(
#         test_utils.MULTIPLE_FUNCTIONS_PY_PATH, do_cleanup=False, backend="serverless"
#     )
#     deploy(
#         test_utils.MULTIPLE_FUNCTIONS_PY_PATH,
#         do_cleanup=True,
#         project_id=project_id,
#         backend="serverless",
#     )
#
#
# def test_integration_deploy_one_existing_function_using_srvless_fw():
#     project_id = deploy(test_utils.APP_PY_PATH, do_cleanup=False, backend="serverless")
#     deploy(
#         test_utils.MULTIPLE_FUNCTIONS_PY_PATH,
#         do_cleanup=True,
#         project_id=project_id,
#         backend="serverless",
#     )
