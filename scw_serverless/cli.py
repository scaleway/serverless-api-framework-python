import os
from pathlib import Path
from typing import Literal, Optional

import click

from scw_serverless.config import generators
from scw_serverless.dependencies_manager import DependenciesManager
from scw_serverless.deploy import backends
from scw_serverless.gateway.gateway_manager import GatewayManager
from scw_serverless.logger import DEFAULT, get_logger
from scw_serverless.utils.credentials import DEFAULT_REGION, get_scw_client
from scw_serverless.utils.loader import get_app_instance

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
    "--backend",
    "-b",
    "backend",
    default="api",
    type=click.Choice(["api", "serverless"], case_sensitive=False),
    show_default=True,
    help="Select the backend used to deploy",
)
@click.option(
    "--no-single-source",
    "single_source",
    is_flag=True,
    default=True,
    help="Do not remove functions not present in the code being deployed",
)
@click.option(
    "--gateway-url",
    "gateway_url",
    default=None,
    help="URL of a deployed API Gateway.",
)
@click.option(
    "--gateway-api-key",
    "gateway_api_key",
    default=None,
    help="API key used to manage the routes of the API Gateway.",
)
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
def deploy(
    file: Path,
    backend: Literal["api", "serverless"],
    single_source: bool,
    gateway_url: Optional[str] = None,
    gateway_api_key: Optional[str] = None,
    profile_name: Optional[str] = None,
    secret_key: Optional[str] = None,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
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

    if not gateway_url:
        raise RuntimeError(
            "Your application requires an API Gateway but no gateway URL was provided"
        )
    if not gateway_api_key:
        raise RuntimeError(
            "Your application requires an API Gateway but "
            + "no gateway API key was provided to manage routes"
        )

    manager = GatewayManager(
        app_instance=app_instance,
        gateway_url=gateway_url,
        gateway_api_key=gateway_api_key,
        sdk_client=client,
    )
    manager.update_routes()


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

    generator = None
    if target == "serverless":
        generator = generators.ServerlessFrameworkGenerator(app_instance)
    elif target == "terraform":
        generator = generators.TerraformGenerator(
            app_instance,
            deps_manager=DependenciesManager(
                file.parent.resolve(), file.parent.resolve()
            ),
        )
    if generator:
        generator.write(save)

    get_logger().success(f"Done! Generated configuration file saved in {save}")


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
