import logging
from pathlib import Path
from typing import Optional, cast

import click
from scaleway import ScalewayException

import scw_serverless
from scw_serverless import app, deployment, loader, local_app, logger
from scw_serverless.dependencies_manager import DependenciesManager
from scw_serverless.gateway import GatewayManager, ServerlessGateway

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
@click.option("--verbose", is_flag=True, help="Enables verbose mode.")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    show_default=True,
    help="Set the log level.",
)
def cli(verbose: bool, log_level: str) -> None:
    """Deploy your Serverless functions on Scaleway's Cloud.

    Documentation:
    https://serverless-api-project.readthedocs.io/en/latest/
    """
    logger.configure_logger(verbose, log_level=getattr(logging, log_level))


@cli.command()
@CLICK_ARG_FILE
@click.option(
    "--runtime",
    default=None,
    help="Python runtime to deploy with. Uses your Python version by default.",
)
@click.option(
    "--single-source",
    is_flag=True,
    default=True,
    help="Remove functions not present in the code being deployed",
)
@click.option(
    "--profile",
    "-p",
    default=None,
    help="Scaleway profile to use when loading credentials.",
)
@click.option(
    "--project-id",
    default=None,
    help="""API Project ID used for the deployment.
WARNING: Please use environment variables instead""",
)
@click.option(
    "--region",
    default=None,
    help="Region to deploy to.",
)
# pylint: disable=too-many-arguments
def deploy(
    file: Path,
    runtime: Optional[str],
    single_source: bool,
    profile: Optional[str] = None,
    secret_key: Optional[str] = None,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
) -> None:
    """Deploy your functions to Scaleway.

    FILE is the file containing your functions handlers

    If the credentials are not provided, the credentials will
    be pulled from your Scaleway configuration.
    """
    # Get the serverless App instance
    app_instance = loader.load_app_instance(file.resolve())

    # Check if the application requires a Gateway
    needs_gateway = any(function.gateway_route for function in app_instance.functions)
    gateway = None
    if needs_gateway:
        logging.debug("Checking for Gateway CLI")
        gateway = ServerlessGateway()

    client = deployment.get_scw_client(profile, secret_key, project_id, region)

    if not runtime:
        runtime = deployment.get_current_runtime()

    logging.info("Packaging dependencies...")
    deps = DependenciesManager(file.parent, Path.cwd())
    deps.generate_package_folder()

    try:
        deployment.DeploymentManager(
            app_instance=app_instance,
            sdk_client=client,
            runtime=runtime,
            single_source=single_source,
        ).deploy()
    except ScalewayException as e:
        logging.debug(e, exc_info=True)
        deployment.log_scaleway_exception(e)

    if needs_gateway:
        assert gateway

        manager = GatewayManager(
            app_instance=app_instance,
            gateway=gateway,
            sdk_client=client,
        )
        manager.update_routes()


@cli.command()
@CLICK_ARG_FILE
@click.option(
    "--port",
    "-p",
    "port",
    default=8080,
    show_default=True,
    help="Set port to listen on.",
)
@click.option(
    "--debug/--no-debug",
    "debug",
    default=True,
    show_default=True,
    help="Run Flask in debug mode.",
)
def dev(file: Path, port: int, debug: bool) -> None:
    """Run functions locally with Serverless Local Testing."""
    app.Serverless = local_app.ServerlessLocal
    scw_serverless.Serverless = local_app.ServerlessLocal
    app_instance = cast(
        local_app.ServerlessLocal, loader.load_app_instance(file.resolve())
    )
    app_instance.local_server.serve(port=port, debug=debug)
