import importlib.util
import inspect
import os
from pathlib import Path
from typing import Literal, Optional

import click

from scw_serverless.app import Serverless
from scw_serverless.config.generators.serverless_framework import (
    ServerlessFrameworkGenerator,
)
from scw_serverless.config.generators.terraform import TerraformGenerator
from scw_serverless.dependencies_manager import DependenciesManager
from scw_serverless.deploy import backends, gateway
from scw_serverless.logger import DEFAULT, get_logger
from scw_serverless.utils.config import Config
from scw_serverless.utils.credentials import DEFAULT_REGION, get_scw_client

CLICK_ARG_FILE = click.argument(
    "file",
    required=True,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
)


@click.group()
def cli() -> None:
    """Deploy your Serverless functions on Scaleway's Cloud.

    Documentation:
    https://serverless-api-project.readthedocs.io/en/latest/
    """


# TODO?: clean up the locals by introducing a class
# pylint: disable=too-many-arguments,too-many-locals
@cli.command()
@CLICK_ARG_FILE
@click.option(
    "--profile",
    "-p",
    "profile_name",
    default=None,
    help="Scaleway profile to use when loading credentials.",
)
@click.option(
    "--secret-key",
    "secret_key",
    default=None,
    help="""API Secret key used for the deployment.
WARNING: Please use environment variables instead""",
)
@click.option(
    "--project-id",
    "project_id",
    default=None,
    help="""API Project ID used for the deployment.
WARNING: Please use environment variables instead""",
)
@click.option(
    "--region",
    "region",
    default=None,
    help=f"Region to deploy to. Default: {DEFAULT_REGION}",
)
@click.option(
    "--no-single-source",
    "single_source",
    is_flag=True,
    default=True,
    help="Do not remove functions not present in the code being deployed",
)
@click.option(
    "--backend",
    "-b",
    "backend",
    default="api",
    type=click.Choice(["api", "serverless"], case_sensitive=False),
    show_default=True,
    help="Select the backend used to deploy",
)
@click.option(
    "--gw-id",
    "-g",
    "gateway_id",
    envvar="SCW_APIGW_ID",
    help="API Gateway uuid to use with function endpoints",
)
@click.option(
    "--api-gw-host",
    envvar="SCW_API_GW_HOST",
    help="Host of the API to manage gateways",
)
def deploy(
    file: Path,
    backend: Literal["api", "serverless"],
    single_source: bool,
    profile_name: Optional[str] = None,
    secret_key: Optional[str] = None,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    gateway_id: Optional[str] = None,
    api_gw_host: Optional[str] = None,
) -> None:
    """Deploy your functions to Scaleway.

    FILE is the file containing your functions handlers

    If the credentials are not provided, the credentials will
    be pulled from your Scaleway configuration.
    """
    logger = get_logger()

    # Get the serverless App instance
    app_instance = get_app_instance(file.resolve())

    client = get_scw_client(profile_name, secret_key, project_id, region)

    logger.default("Packaging dependencies...")
    DependenciesManager(file.parent, Path("./")).generate_package_folder()

    deploy_backend: Optional[backends.ServerlessBackend] = None
    if backend == "api":
        logger.info("Using the API backend")
        deploy_backend = backends.ScalewayApiBackend(
            app_instance, client, single_source=single_source
        )
    elif backend == "serverless":
        logger.info("Using the Serverless Framework backend")
        deploy_backend = backends.ServerlessFrameworkBackend(app_instance, client)
    if not deploy_backend:
        logger.warning(f"Unknown backend selected: {backend}")

    deploy_backend.deploy()

    needs_gateway = any(function.gateway_route for function in app_instance.functions)
    if not needs_gateway:
        return
    config = Config(api_gw_host, gateway_id).update_from_config_file()
    # If gateway_id is not configured, gateway_domains needs to be set
    is_gateway_configured = config.gateway_id or app_instance.gateway_domains
    if not is_gateway_configured:
        raise RuntimeError(
            "Deploying a routed functions requires a"
            + "gateway_id or a gateway_domain to be configured"
        )
    if not config.api_gw_host:
        raise RuntimeError("No api gateway host was configured")
    # Update the gateway
    manager = gateway.GatewayManager(
        app_instance,
        client,
        config.gateway_id,
        gateway.GatewayClient(config.api_gw_host),
    )
    manager.update_gateway_routes()


@cli.command()
@CLICK_ARG_FILE
@click.option(
    "--target",
    "-t",
    "target",
    default="serverless",
    type=click.Choice(["serverless", "terraform"], case_sensitive=False),
    show_default=True,
    help="Select the configuration type to generate",
)
@click.option(
    "--save",
    "-s",
    "save",
    default="./",
    type=click.Path(file_okay=False, dir_okay=True),
    show_default=True,
    help="Select where to save the generated configuration file",
)
def generate(file: Path, target: str, save: str) -> None:
    """Generate configuration files to deploy your functions.

    FILE is the file containing your functions handlers
    """

    app_instance = get_app_instance(file)  # Get the serverless App instance

    get_logger().default(f"Generating configuration for target: {target}")

    if not os.path.exists(save):
        os.mkdir(save)

    if target == "serverless":
        serverless_framework_generator = ServerlessFrameworkGenerator(app_instance)
        serverless_framework_generator.write(save)
    elif target == "terraform":
        terraform_generator = TerraformGenerator(
            app_instance,
            deps_manager=DependenciesManager(
                file.parent.resolve(), file.parent.resolve()
            ),
        )
        terraform_generator.write(save)

    get_logger().success(f"Done! Generated configuration file saved in {save}")


def get_app_instance(file: Path) -> Serverless:
    """Load the app instance from the client module."""

    file = file.resolve()
    module_name = (
        str(file.relative_to(Path(".").resolve())).removesuffix(".py").replace("/", ".")
    )

    # Importing user's app
    spec = importlib.util.spec_from_file_location(module_name, file)
    user_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_app)

    app_instance = None

    for member in inspect.getmembers(user_app):
        if isinstance(member[1], Serverless):
            # Ok. Found the variable now, need to use it
            app_instance = member[1]

    if not app_instance:  # No variable with type "Serverless" found
        raise RuntimeError(
            f"""Unable to locate an instance of serverless App
            in the provided file: {file}."""
        )

    return app_instance


def main() -> int:
    """Entrypoint for click"""
    # Set logging level to DEFAULT. (ignore debug)
    get_logger().set_level(DEFAULT)
    try:
        cli()
        return 0
    except Exception as exception:  # pylint: disable=broad-except
        get_logger().critical(str(exception))
        return 2
