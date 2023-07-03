import shutil
import subprocess

import click

from scw_serverless.config.route import GatewayRoute

GATEWAY_CLI = "scwgw"
GATEWAY_PYPI = "scw-gateway"


class ServerlessGateway:
    """Manage routes on a Kong Gateway with scwgw."""

    cli: str

    def __init__(self) -> None:
        cli = shutil.which(GATEWAY_CLI)

        if not cli:
            click.secho(
                f"{GATEWAY_CLI} was not found in $PATH, "
                + f"you can install {GATEWAY_CLI} by running:\n"
                + f"pip install {GATEWAY_PYPI}",
                fg="red",
            )
            raise RuntimeError(f"{GATEWAY_CLI} is not installed")

        self.cli = cli

    def _invoke_cli(self, args: list[str]) -> subprocess.CompletedProcess:
        cmd = subprocess.run(
            args=[self.cli] + args,
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        return cmd

    def add_route(self, route: GatewayRoute) -> None:
        """Add a route to the gateway with the CLI."""

        if not route.target:
            raise RuntimeError(f"route {route.relative_url} is missing upstream target")

        cli_args = ["route", "add", route.relative_url, route.target]
        for method in route.http_methods or []:
            cli_args += ["--http-methods", method.value]

        cmd = self._invoke_cli(cli_args)
        for char in cmd.stdout:
            print(char, end="")
