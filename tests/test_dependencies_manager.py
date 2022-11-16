import os
import shutil
import tempfile

import pytest

from scw_serverless.dependencies_manager import DependenciesManager


@pytest.fixture(name="pkg_parent_folder")
def clean_up_pkg_folder():
    folder = tempfile.mkdtemp()
    req_path = os.path.join(folder, "requirements.txt")
    # Writing a stub requirements file
    with open(req_path, "w") as fp:
        fp.write(
            """
        PyYAML==6.0
        """
        )
    try:
        yield folder
    finally:
        shutil.rmtree(folder)


def test_dependencies_manager_generate_package_folder(pkg_parent_folder):
    manager = DependenciesManager(pkg_parent_folder, pkg_parent_folder)
    manager.generate_package_folder()

    assert "package" in os.listdir(pkg_parent_folder)
    installed = os.listdir(os.path.join(pkg_parent_folder, "package"))
    print(installed)

    assert "yaml" in installed
    assert "scw_serverless" in installed
