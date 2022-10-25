from typing import Optional

import os, sys
import pathlib
import subprocess

from .logger import get_logger

REQUIREMENTS_NAME = "requirements.txt"


def _raise_on_pip_process_err(process: subprocess.CompletedProcess) -> None:
    if process.returncode != 0:
        raise RuntimeError(
            "pip exited with non-zero return code:\n %s"
            % process.stdout.decode("UTF-8"),
        )


class DependenciesManager:
    """
    Dependencies Manager

    This class looks for a requirements file in a given input path and
    vendors the pip dependencies in a package folder within the provided output path.

    It does not currently handles native dependencies.

    See also: https://developers.scaleway.com/en/products/functions/api/#python-additional-dependencies
    """

    def __init__(self, in_path: str, out_path: str) -> None:
        self.in_path = pathlib.Path(in_path)
        self.out_path = pathlib.Path(out_path)
        self.logger = get_logger()

    @property
    def pkg_path(self) -> pathlib.Path:
        return self.out_path.joinpath("package")

    def generate_package_folder(self):
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
            self.logger.warning(
                "File %s not found in directory %s"
                % (REQUIREMENTS_NAME, self.in_path.absolute())
            )
        elif self.in_path.is_file():
            # We only check the extension
            if self.in_path.suffix == ".txt":
                return self.in_path.resolve()
            raise ValueError("file %s is not a txt file" % self.in_path.absolute)
        else:
            self.logger.warning(
                "could not find a requirements file in %s" % self.out_path.absolute
            )
            return None

    def _install_requirements(self, requirements_path: pathlib.Path):
        if not self.out_path.is_dir():
            raise ValueError(
                "out_path %s is not a directory p" % self.out_path.absolute
            )
        python_path = sys.executable
        process = subprocess.run(
            [
                python_path,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements_path.resolve()),
                "--target",
                str(self.pkg_path.resolve()),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(self.out_path.resolve()),
        )
        _raise_on_pip_process_err(process)

    def _check_for_scw_serverless(self):
        # We need to load the scw_serveless package somehow
        if (
            not self.pkg_path.exists()
            or not self.pkg_path.joinpath(__package__).exists()
        ):
            # scw_serveless was not installed in the packages folder
            p = pathlib.Path(__file__).parent.parent.resolve()
            python_path = sys.executable
            process = subprocess.run(
                [
                    python_path,
                    "-m",
                    "pip",
                    "install",
                    str(p.resolve()),
                    "--target",
                    str(self.pkg_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(self.out_path.resolve()),
            )
            _raise_on_pip_process_err(process)
