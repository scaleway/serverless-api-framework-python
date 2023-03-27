import re
import shutil
import tempfile
from pathlib import Path
from typing import Literal

from scaleway import Client

from tests.integrations.utils import run_cli, trigger_function

FunctionUrl = str


def run_deploy_command(
    client: Client,
    app_path: Path,
    *args,
    backend: Literal["serverless", "api"] = "api",
) -> list[FunctionUrl]:
    """Run deploy command with a specific backend."""

    app_dir = app_path.parent.resolve()

    # Run the command inside a temporary directory
    with tempfile.TemporaryDirectory() as directory:
        shutil.copytree(src=app_dir, dst=directory, dirs_exist_ok=True)

        cmd = ["deploy", app_path.name, "-b", backend]
        cmd.extend(args)
        ret = run_cli(client, directory, cmd)

    assert ret.returncode == 0, f"Non-null return code: {ret}"

    output = ret.stderr if backend == "serverless" else ret.stdout
    output = str(output.decode("UTF-8")).strip()

    # Parse the functions URL from the program output
    pattern = re.compile(
        r"(Function [a-z0-9-]+ (?:has been )?deployed to:? (https://.+))"
    )
    groups = re.findall(pattern, output)

    function_urls = []
    for group in groups:
        function_urls.append(group[1])

        # Call the actual function
        trigger_function(group[1])

    return function_urls
