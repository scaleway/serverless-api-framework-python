from pathlib import Path
from typing import Tuple

import tests.utils as test_utils
from scw_serverless.dependencies_manager import DependenciesManager

# pylint: disable=unused-import # fixture
from tests.integrations.utils import (  # noqa: F401
    _create_serverless_project,
    deploy,
    serverless_framework,
)


def test_integration_serverless_framework(serverless_project: Tuple[str, str]):
    deps = DependenciesManager(Path("./"), Path("./"))
    deps.generate_package_folder()

    serverless_framework(test_utils.APP_PY_PATH, serverless_project=serverless_project)


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
