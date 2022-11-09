import importlib.util
import inspect
import os.path

from typing import Optional

import click

from scw_serverless.app import Serverless
from scw_serverless.api import Api
from scw_serverless.config.generators.serverlessframework import (
    ServerlessFrameworkGenerator,
)
from scw_serverless.config.generators.terraform import TerraformGenerator
from scw_serverless.dependencies_manager import DependenciesManager
import scw_serverless.deploy.backends as backends
import scw_serverless.deploy.gateway as gateway

from scw_serverless.logger import get_logger, DEFAULT
from scw_serverless.utils.credentials import find_scw_credentials
from scw_serverless.utils.config import Config


@click.group()
def cli():
    pass


@cli.command(help="Deploy your functions to scaleway")
@click.option(
    "--file",
    "-f",
    "file",
    default="app.py",
    show_default=True,
    help="Select the file containing your functions handlers",
)
@click.option(
    "--secret-key",
    "secret_key",
    default=None,
    help="API Secret key used for the deployment. WARNING: Please use environment variables instead",
)
@click.option(
    "--project-id",
    "project_id",
    default=None,
    help="API Project ID used for the deployment. WARNING: Please use environment variables instead",
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
    file: str,
    backend: str,
    single_source: bool,
    secret_key: Optional[str] = None,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    gw_id: Optional[str] = None,
    api_gw_host: Optional[str] = None,
):
    config = Config(api_gw_host=api_gw_host, gateway_id=gw_id)
    config = config.update_from_config_file()

    # Get the serverless App instance
    app_instance = get_app_instance(file)

    # If the credentials were not provided as option, look for them in configuration file or
    # system environment variables
    if secret_key is None or project_id is None or region is None:
        secret, project, reg = find_scw_credentials()
        if secret_key is None:  # Secret key is None, update it
            secret_key = secret
        if project_id is None:  # Project id is None, update it
            project_id = project
        if region is None:  # Region is None, update id
            region = reg

    if region is None:
        region = "pl-waw"  # If the region is still not defined, update it to fr-par

    if secret_key is None or project_id is None:
        # No credentials were provided, abort
        raise RuntimeError("Unable to find credentials for deployment.")

    # Create the deploy configuration
    deploy_config = backends.DeployConfig(project_id, secret_key, region)

    get_logger().default("Packaging dependencies...")
    deps = DependenciesManager("./", "./")
    deps.generate_package_folder()

    b = None  # Select the request backend
    if backend == "api":
        # Deploy using the scaleway api
        get_logger().info("Using the API backend")
        b = backends.ScalewayApiBackend(
            app_instance=app_instance,
            single_source=single_source,
            deploy_config=deploy_config,
        )
    elif backend == "serverless":
        # Deploy using the serverless framework
        get_logger().info("Using the Serverless Framework backend")
        b = backends.ServerlessFrameworkBackend(
            app_instance=app_instance, deploy_config=deploy_config
        )
    if b:
        b.deploy()

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


@cli.command(help="Generate the configuration file for your functions")
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
    "--file",
    "-f",
    "file",
    default="app.py",
    show_default=True,
    help="Select the file containing your functions handlers",
)
@click.option(
    "--save",
    "-s",
    "save",
    default="./",
    show_default=True,
    help="Select where to save the generated configuration file",
)
def generate(file, target, save):
    app_instance = get_app_instance(file)  # Get the serverless App instance

    get_logger().default(f"Generating configuration for target: {target}")

    if not os.path.exists(save):
        os.mkdir(save)

    if target == "serverless":
        serverless_framework_generator = ServerlessFrameworkGenerator(app_instance)
        serverless_framework_generator.write(save)
    elif target == "terraform":
        # TODO: Change this to a configurable path
        terraform_generator = TerraformGenerator(
            app_instance, deps_manager=DependenciesManager("./", "./")
        )
        terraform_generator.write(save)

    get_logger().success(f"Done! Generated configuration file saved in {save}")


def get_app_instance(file: str) -> Serverless:
    abs_file = os.path.abspath(file)

    if not os.path.exists(abs_file):
        raise RuntimeError(
            "The provided file doesn't seem to exist. Please provide a valid python file with -f."
        )

    module_name = (
        abs_file.replace(os.path.abspath("./"), "").split(".")[0].replace("/", ".")
    )[
        1:
    ]  # This is more a "temporary hack" than a real solution.

    # Importing user's app
    spec = importlib.util.spec_from_file_location(module_name, abs_file)
    user_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_app)

    app_instance = None

    for member in inspect.getmembers(user_app):
        if isinstance(member[1], Serverless):
            # Ok. Found the variable now, need to use it
            app_instance = member[1]

    if app_instance is None:  # No variable with type "Serverless" found
        raise RuntimeError(
            "Unable to locate an instance of serverless App in the provided file."
        )

    return app_instance


def main():
    # Set logging level to DEFAULT. (ignore debug)
    get_logger().set_level(DEFAULT)
    try:
        return cli()
    except Exception as ex:
        get_logger().critical(str(ex))
        return 2
