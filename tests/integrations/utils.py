import os
import random
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Iterable, Optional

import pytest
import requests
import yaml
from requests import HTTPError
from scaleway import Client
from scaleway.account.v2 import AccountV2API
from scaleway.function.v1beta1 import FunctionV1Beta1API
from scaleway.registry.v1 import RegistryV1API
from scaleway_core.api import ScalewayException
from typing_extensions import Self

from scw_serverless.dependencies_manager import DependenciesManager

DEFAULT_REGION = "pl-waw"
CLI_COMMAND = "srvless"


class ServerlessTestProject:
    """
    ServerlessTestProject encapsulates the logic of
    setting up a clean integration test environment.

    For each test, we:
        - Create a Scaleway project.
        - Copy the target path to a temporary directory.
          This avoids build artifacts pollution when
          deploying the same app concurrently.
        - Run the test.
        - Validate that the functions have been deployed.
        - Delete the temporary directory.
        - Clean up the project.
          We delete all remaining namespaces/functions/registries.
    """

    def __init__(self) -> None:
        client = Client.from_config_file_and_env()
        if not client.default_region:
            client.default_region = DEFAULT_REGION
        self.client = client
        self.project_id: Optional[str] = None

    def deploy(self, app: str, backend: str):
        """Run deploy command with a specific backend."""

        app_path = Path(app)
        app_dir = app_path.parent.resolve()

        # Run the command inside a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copytree(src=app_dir, dst=tmpdir, dirs_exist_ok=True)

            ret = self._run_srvless_cli(
                tmpdir, ["deploy", app_path.name, "-b", backend]
            )

        assert ret.returncode == 0, f"Non-null {CLI_COMMAND} return code: {ret}"

        output = str(ret.stdout.decode("UTF-8")).strip()
        if backend == "serverless":
            # serverless framework print normal output on stderr
            output = str(ret.stderr.decode("UTF-8")).strip()

        # Parse the functions URL from the program output
        pattern = re.compile(
            r"(Function [a-z0-9-]+ (?:has been )?deployed to:? (https://.+))"
        )
        groups = re.findall(pattern, output)

        assert len(groups) > 0, output  # Avoids silent errors
        for group in groups:
            # Call the actual function
            call_function(group[1])

    def generate_serverless_framework(self, app: str):
        """Run the generate command with the serverless backend."""

        # Verify that serverless and node are installed and available
        serverless_path = shutil.which("serverless")
        assert serverless_path
        node_path = shutil.which("node")
        assert node_path

        app_path = Path(app)
        app_dir = app_path.parent.resolve()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Even with a minimal example, packaging is required
            # so that scw_serverless is available in the function env
            deps = DependenciesManager(Path(tmpdir), Path(tmpdir))
            deps.generate_package_folder()

            shutil.copytree(src=app_dir, dst=tmpdir, dirs_exist_ok=True)
            ret = self._run_srvless_cli(
                tmpdir, ["generate", app_path.name, "-t", "serverless"]
            )
            assert ret.returncode == 0, f"Non-null {CLI_COMMAND} return code: {ret}"
            output = str(ret.stdout.decode("UTF-8")).strip()
            assert "Done" in output, f"Done not found in output: {output}"

            ret = subprocess.run(
                [node_path, serverless_path, "deploy"],
                env={
                    "SCW_SECRET_KEY": self.client.secret_key,
                    "SCW_DEFAULT_PROJECT_ID": self.project_id,
                    "SCW_REGION": self.client.default_region,
                },  # type: ignore // client already validated
                capture_output=True,
                cwd=tmpdir,
                check=False,
            )

        assert ret.returncode == 0, f"Non-null serverless return code: {ret}"

        # Parse the functions URL from the program output
        output = str(ret.stderr.decode("UTF-8")).strip()
        pattern = re.compile("(Function [a-z0-9-]+ has been deployed to: (https://.+))")
        groups = re.findall(pattern, output)

        assert len(groups) > 0  # Avoids silent errors
        for group in groups:
            # Call the actual function
            call_function(group[1])

    def generate_terraform(self, app: str):
        """Run the generate command with the serverless backend."""

        # Verify that terraform is installed and availabke
        terraform_path = shutil.which("terraform")
        assert terraform_path
        app_path = Path(app)
        app_dir = app_path.parent.resolve()

        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copytree(src=app_dir, dst=tmpdir, dirs_exist_ok=True)
            ret = self._run_srvless_cli(
                tmpdir, ["generate", app_path.name, "-t", "terraform"]
            )
            assert ret.returncode == 0, print(ret)
            assert "Done" in str(ret.stdout.decode("UTF-8")).strip(), print(ret)
            subprocess.run([terraform_path, "init"], cwd=tmpdir, check=True)

            config_path = str(Path(tmpdir).joinpath("/scw.yaml").resolve())
            write_scw_config(self.client, config_path)
            subprocess.run(
                [terraform_path, "validate"],
                env={
                    "TF_VAR_project_id": self.project_id,
                    "SCW_CONFIG_PATH": config_path,
                },  # type: ignore // client already validated
                capture_output=True,
                check=True,
            )

    def _run_srvless_cli(self, cwd: str, args: list[str]):
        cli = shutil.which(CLI_COMMAND)
        assert cli
        return subprocess.run(
            [cli] + args,
            env={
                "SCW_SECRET_KEY": self.client.secret_key,
                "SCW_ACCESS_KEY": self.client.access_key,
                "SCW_DEFAULT_PROJECT_ID": self.project_id,
                "SCW_DEFAULT_REGION": self.client.default_region,
                "PATH": os.environ["PATH"],
            },  # type: ignore // client already validated
            capture_output=True,
            # Runs the cli in the tests directory
            cwd=cwd,
            check=False,  # Checked in the tests
        )

    def __enter__(self) -> Self:
        self.project_id = self._create_project()
        return self

    def _create_project(self) -> str:
        sha = os.getenv("GITHUB_SHA", "local")
        name = f"apifw-{sha[:7]}-{random.randint(0, 9999)}"
        project = AccountV2API(self.client).create_project(
            name,
            description="Created by the Serverless API Framework integration suite.",
        )
        return project.id

    def __exit__(self, _type, _value, _traceback):  # noqa: ANN001
        self._delete_resources()
        self._delete_project()
        return True

    def _delete_resources(self):
        """Delete all Scaleway resources created in the temporary project."""
        if not self.project_id:
            return
        api = FunctionV1Beta1API(self.client)
        namespaces = api.list_namespaces_all(project_id=self.project_id)
        for namespace in namespaces:
            api.delete_namespace(namespace_id=namespace.id)
        registry_api = RegistryV1API(self.client)
        registries = registry_api.list_namespaces_all(project_id=self.project_id)
        for registry in registries:
            registry_api.delete_namespace(namespace_id=registry.id)
        # All deletions have been scheduled,
        # we can wait for their completion sequentially
        for namespace in namespaces:
            try:
                api.wait_for_namespace(namespace_id=namespace.id)
            except ScalewayException as e:
                if e.status_code != 404:
                    raise e
        for registry in registries:
            try:
                registry_api.wait_for_namespace(namespace_id=registry.id)
            except ScalewayException as e:
                if e.status_code != 404:
                    raise e

    def _delete_project(self, max_tries: int = 5):
        if not self.project_id:
            return
        api = AccountV2API(self.client)
        for _ in range(max_tries):
            try:
                api.delete_project(self.project_id)
                return
            except ScalewayException as e:
                # This is just very finicky, the account API is somewhat unstable.
                print(e)
                time.sleep(30)


@pytest.fixture
def serverless_test_project() -> Iterable[ServerlessTestProject]:
    with ServerlessTestProject() as project:
        yield project


def call_function(url: str, max_retries: int = 5):
    retry_delay = 5
    raised_ex = None
    for _ in range(max_retries):
        raised_ex = None
        try:  # Call the function
            req = requests.get(url, timeout=retry_delay)
            req.raise_for_status()
            break
        except ConnectionError as exception:
            time.sleep(retry_delay)
            raised_ex = exception
        except HTTPError as exception:
            raised_ex = exception
            # If the request as timed out
            if exception.response.status_code != 408:
                break
            time.sleep(retry_delay)
    if raised_ex:
        raise raised_ex


def write_scw_config(client: Client, config_path: str):
    with open(config_path, mode="wt", encoding="utf-8") as fp:
        yaml.dump(
            {
                "access_key": client.access_key,
                "secret_key": client.secret_key,
                "default_region": client.default_region,
            },
            fp,
        )
