import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

import pytest

from scw_serverless.dependencies_manager import DependenciesManager


@pytest.fixture(name="pkg_folder")
def clean_up_pkg_folder() -> Iterable[Path]:
    folder = Path(tempfile.mkdtemp())
    try:
        yield folder
    finally:
        shutil.rmtree(folder)


def test_dependencies_manager_generate_package_folder(pkg_folder: Path):
    req_path = pkg_folder.joinpath("requirements.txt")
    with open(req_path, mode="w", encoding="utf-8") as fp:
        fp.write("PyYAML==6.0\n" + "scw_serverless==0.0.1b")

    manager = DependenciesManager(pkg_folder, pkg_folder)
    manager.generate_package_folder()

    assert "package" in os.listdir(pkg_folder)
    installed = os.listdir(os.path.join(pkg_folder, "package"))

    assert "yaml" in installed
    assert "scw_serverless" in installed


def test_dependencies_manager_install_scw_from_local(pkg_folder: Path):
    req_path = pkg_folder.joinpath("requirements.txt")
    with open(req_path, mode="w", encoding="utf-8") as fp:
        fp.write("PyYAML==6.0")

    manager = DependenciesManager(pkg_folder, pkg_folder)
    manager.generate_package_folder()

    assert "package" in os.listdir(pkg_folder)
    installed = os.listdir(os.path.join(pkg_folder, "package"))

    assert "yaml" in installed
    assert "scw_serverless" in installed
