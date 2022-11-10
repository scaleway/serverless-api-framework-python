import importlib.util
import inspect
import os.path
from pathlib import Path
from typing import Optional

import click

from scw_serverless.api import Api
from scw_serverless.app import Serverless
from scw_serverless.config.generators.serverlessframework import (
    ServerlessFrameworkGenerator,
)
from scw_serverless.config.generators.terraform import TerraformGenerator
from scw_serverless.dependencies_manager import DependenciesManager
from scw_serverless.deploy import backends, gateway
from scw_serverless.logger import DEFAULT, get_logger
from scw_serverless.utils.config import Config
from scw_serverless.utils.credentials import find_scw_credentials

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
    default="app.py",
)


@click.group()
def cli() -> None:
    """Main command group"""


# TODO?: clean up the locals by introducing a class
# pylint: disable=too-many-arguments,too-many-locals
@cli.command()
@CLICK_ARG_FILE
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
    help="Region to deploy to. Default: fr-par",
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
    envvar="SCW_API_GW_ID",
    help="API Gateway uuid to use with function endpoints",
)
@click.option(
    "--api_gw_host",
    envvar="SCW_API_GW_HOST",
    help="Host of the API to manage gateways",
)
def deploy(
    file: Path,
    backend: str,
    single_source: bool,
    secret_key: Optional[str] = None,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    gw_id: Optional[str] = None,
    api_gw_host: Optional[str] = None,
) -> None:
    """Deploy your functions to Scaleway.

    FILE is the file containing your functions handlers

    If the credentials are not provided, the credentials will
    be pulled from your Scaleway configuration.
    """
    logger = get_logger()

    config = Config(api_gw_host=api_gw_host, gateway_id=gw_id)
    config = config.update_from_config_file()

    # Get the serverless App instance
    app_instance = get_app_instance(file.resolve())

    # If the credentials were not provided as option,
    # look for them in configuration file or system environment variables
    if not all([secret_key, project_id, region]):
        secret, project, reg = find_scw_credentials()
        # Update the missing values
        secret_key = secret_key if secret_key else secret
        project_id = project_id if project_id else project
        region = region if region else reg

    region = region if region else "fr-par"  # Defaults to to fr-par

    if not all([secret_key, project_id]):
        # No credentials were provided, abort
        raise RuntimeError("Unable to find credentials for deployment.")

    # Create the deploy configuration
    deploy_config = backends.DeployConfig(project_id, secret_key, region)

    logger.default("Packaging dependencies...")
    deps = DependenciesManager(file.parent, file.parent)
    deps.generate_package_folder()

    deploy_backend = None  # Select the request backend
    if backend == "api":
        # Deploy using the scaleway api
        logger.info("Using the API backend")
        deploy_backend = backends.ScalewayApiBackend(
            app_instance=app_instance,
            single_source=single_source,
            deploy_config=deploy_config,
        )
    elif backend == "serverless":
        # Deploy using the serverless framework
        logger.info("Using the Serverless Framework backend")
        deploy_backend = backends.ServerlessFrameworkBackend(
            app_instance=app_instance, deploy_config=deploy_config
        )
    if not deploy_backend:
        logger.warning(f"Unknown backend selected: {backend}")

    deploy_backend.deploy()
    # If gateway_id is not configured, gateway_domains needs to be set
    is_gateway_configured = config.gateway_id or app_instance.gateway_domains
    contains_routed_func = any(filter(app_instance.functions, lambda f: f.get_path()))

    if contains_routed_func and not is_gateway_configured:
        raise RuntimeError(
            """Deploying a routed functions requires a
                     gateway_id or a gateway_domain to be configured."""
        )

    # Update the gateway
    api = Api(region=region, secret_key=secret_key)
    manager = gateway.GatewayManager(
        app_instance,
        api,
        project_id,
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
    """Generate configuration files for your functions

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
        return cli()
    except Exception as ex:  # pylint: disable=broad-except
        get_logger().critical(str(ex))
        return 2
