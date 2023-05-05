import logging
import os
import pathlib
import re
import subprocess
import sys
from importlib.metadata import version
from typing import Optional

REQUIREMENTS_NAME = "requirements.txt"

logger = logging.getLogger(__name__)


class DependenciesManager:
    """Dependencies Manager vendors the python dependencies.

    This class looks for a requirements file in a given input path and
    vendors the pip dependencies in a package folder within the provided output path.

    It does not currently handles native dependencies.

    .. seealso::

        Scaleway Documentation
        <https://developers.scaleway.com/en/products/functions/api/#python-additional-dependencies>
    """

    def __init__(
        self, in_path: pathlib.Path, out_path: pathlib.Path, runtime: str
    ) -> None:
        self.in_path = in_path
        self.out_path = out_path
        self.runtime_version = "310"
        version_pattern = r"python(\d+)"
        if match := re.search(version_pattern, runtime):
            self.runtime_version = str(match.group(1))

    @property
    def pkg_path(self) -> pathlib.Path:
        """Path to the package directory to vendor the deps into."""
        return self.out_path.joinpath("package")

    def generate_package_folder(self) -> None:
        """Generates a package folder with vendored pip dependencies."""
        requirements = self._find_requirements()
        if requirements is not None:
            self._install_requirements(requirements)
        self._check_for_scw_serverless()

    def _find_requirements(self) -> Optional[pathlib.Path]:
        if self.in_path.is_dir():
            for file in os.listdir(self.in_path):
                fp = pathlib.Path(self.in_path.joinpath(file))
                if fp.is_file() and fp.name == REQUIREMENTS_NAME:
                    return fp.resolve()
            logger.warning(
                "File %s not found in %s", REQUIREMENTS_NAME, self.in_path.absolute()
            )
            return None
        if self.in_path.is_file():
            # We only check the extension
            if self.in_path.suffix == ".txt":
                return self.in_path.resolve()
            raise ValueError(f"File {self.in_path.absolute} is not a txt file")
        logger.warning(
            "Could not find a requirements file in %s", self.out_path.absolute
        )
        return None

    def _install_requirements(self, requirements_path: pathlib.Path):
        if not self.out_path.is_dir():
            raise ValueError(f"Out_path: {self.out_path.absolute} is not a directory")
        logging.debug("Install dependencies from requirements to %s", self.pkg_path)
        self._run_pip_install(
            "-r",
            str(requirements_path.resolve()),
            "--python-version",
            self.runtime_version,
            "--only-binary=:all:",
        )

    def _check_for_scw_serverless(self):
        """Checks for scw_serverless after vendoring the dependencies."""
        if (
            not self.pkg_path.exists()
            or not self.pkg_path.joinpath(__package__).exists()
        ):
            # Installs the current version with pip
            logging.debug("Installing %s from pip to %s", __package__, self.pkg_path)
            self._run_pip_install(
                f"{__package__}~={version(__package__)}",
                "--python-version",
                self.runtime_version,
                "--only-binary=:all:",
            )

    def _run_pip_install(self, *args: str):
        python_path = sys.executable
        command = [
            python_path,
            "-m",
            "pip",
            "install",
            *args,
            "--target",
            str(self.pkg_path.resolve()),
        ]

        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.out_path.resolve()),
            )
        except subprocess.CalledProcessError as e:
            logger.debug(e, exc_info=True)
            logger.error("Error when running: %s", " ".join(command))
            raise RuntimeError(e.stderr) from e
