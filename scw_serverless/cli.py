import importlib.util
import inspect
import os.path
import sys
import traceback

import click
import requests

from scw_serverless.api import Api
from scw_serverless.app import Serverless
from scw_serverless.config.generators.serverlessframework import (
    ServerlessFrameworkGenerator,
)
from scw_serverless.utils import find_scw_credentials, create_zip_file


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
def deploy(file, secret_key: str = None, project_id: str = None, region: str = None):
    app_instance = get_app_instance(file)  # Get the serverless App instance

    # if the credentials were not provided as option, look for them in configuration file or
    #  system environment variables
    if secret_key is None or project_id is None or region is None:
        secret, project, reg = find_scw_credentials(lambda l: click.echo(l))
        if secret_key is None:  # Secret key is None, update it
            secret_key = secret
        if project_id is None:  # Project id is None, update it
            project_id = project
        if region is None:  # Region is None, update id
            region = reg

    if region is None:
        region = "fr-par"  # If the region is still not defined, update it to fr-par

    if secret_key is None or project_id is None:
        raise RuntimeError

    api = Api(region=region, secret_key=secret_key)  # Init the API Client

    namespace = None

    click.echo(
        f"Looking for an existing namespace {app_instance.service_name} in {api.region}..."
    )
    for ns in api.list_namespaces(
        project_id
    ):  # Search in the user's namespace if one is matching the same name and region
        if ns["name"] == app_instance.service_name:
            namespace = ns["id"]

    new_namespace = False

    if namespace is None:
        click.echo(
            f"Creating a new namespace {app_instance.service_name} in {api.region}..."
        )
        ns = api.create_namespace(  # Create a new namespace
            app_instance.service_name,
            project_id,
            app_instance.env,
            None,  # Description
            app_instance.secret,
        )

        if ns is None:
            raise RuntimeError("Unable to create a new namespace")

        namespace = ns["id"]
        new_namespace = True

    version = f"{sys.version_info.major}{sys.version_info.minor}"  # Get the python version from the current env
    click.echo(f"Using python{version}")

    # Create a ZIP archive containing the entire project
    click.echo("Creating a deployment archive...")
    if not os.path.exists("./.scw"):
        os.mkdir("./.scw")

    if os.path.exists("./.scw/deployment.zip"):
        os.remove("./.scw/deployment.zip")

    create_zip_file("./.scw/deployment.zip", "./")
    file_size = os.path.getsize("./.scw/deployment.zip")

    for func in app_instance.functions:  # For each function
        click.echo(f"Looking for an existing function {func['function_name']}...")
        target_function = None
        domain = None

        for fn in api.list_functions(
            namespace_id=namespace
        ):  # Looking if a function is already existing
            if fn["name"] == func["function_name"]:
                target_function = fn["id"]
                domain = fn["domain_name"]

        if target_function is None:
            click.echo(f"Creating a new function {func['function_name']}...")
            fn = api.create_function(  # TODO: FIXME: Try to refactor this as it is not very readable...
                namespace_id=namespace,
                name=func["function_name"],
                runtime=f"python{version}",
                handler=func["handler"],
                privacy=func["args"]["privacy"]
                if func["args"]["privacy"] is not None
                else "unknown_privacy",
                env=func["args"]["env"] if func["args"]["env"] is not None else None,
                min_scale=func["args"]["min_scale"]
                if func["args"]["min_scale"] is not None
                else None,
                max_scale=func["args"]["max_scale"]
                if func["args"]["max_scale"] is not None
                else None,
                memory_limit=func["args"]["memory_limit"]
                if func["args"]["memory_limit"] is not None
                else None,
                timeout=func["args"]["timeout"]
                if func["args"]["timeout"] is not None
                else None,
                description=func["args"]["description"]
                if func["args"]["description"] is not None
                else None,
                secrets=func["args"]["secret"]
                if func["args"]["secret"] is not None
                else None,
            )

            if fn is None:
                raise RuntimeError("Unable to create a new function")

            target_function = fn["id"]
            domain = fn["domain_name"]
        else:
            api.update_function(  # TODO: FIXME: Try to refactor this as it is not very readable...
                function_id=target_function,
                runtime=f"python{version}",
                handler=func["handler"],
                privacy=func["args"]["privacy"]
                if func["args"]["privacy"] is not None
                else "unknown_privacy",
                env=func["args"]["env"] if func["args"]["env"] is not None else None,
                min_scale=func["args"]["min_scale"]
                if func["args"]["min_scale"] is not None
                else None,
                max_scale=func["args"]["max_scale"]
                if func["args"]["max_scale"] is not None
                else None,
                memory_limit=func["args"]["memory_limit"]
                if func["args"]["memory_limit"] is not None
                else None,
                timeout=func["args"]["timeout"]
                if func["args"]["timeout"] is not None
                else None,
                description=func["args"]["description"]
                if func["args"]["description"] is not None
                else None,
                secrets=func["args"]["secret"]
                if func["args"]["secret"] is not None
                else None,
            )

        # Get an object storage pre-signed url
        upload_url = api.upload_function(
            function_id=target_function, content_length=file_size
        )

        click.echo("Uploading function")
        with open(".scw/deployment.zip", "rb") as file:
            req = requests.post(
                upload_url,
                files={"file": (f"function-{target_function}.zip", file)},
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(file_size),
                },
            )

            if req.status_code != 200:
                click.echo(
                    click.style(
                        "Unable to upload function code... Aborting...",
                        fg="red",
                    ),
                    err=True,
                )
                raise RuntimeError("Unable to upload file")

        if not api.deploy_function(target_function):
            click.echo(
                click.style(
                    f"Unable to deploy function {func['function_name']}...",
                    fg="red",
                ),
                err=True,
            )
        else:
            click.echo(
                click.style(
                    f"Function {func['function_name']} has been deployed to {domain}",
                    fg="green",
                )
            )

    if not new_namespace:
        click.echo("Updating namespace configuration")
        api.update_namespace(  # Update the namespace
            app_instance.env,
            None,  # Description
            app_instance.secret,
        )

    click.echo(
        click.style(f"Done! Functions have been successfully deployed!", fg="green")
    )


@cli.command(help="Generate the configuration file for your functions")
@click.option(
    "--target",
    "-t",
    "target",
    default="serverless",
    type=click.Choice(["serverless"], case_sensitive=False),
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

    click.echo(f"Generating configuration for target: {target}")

    if target == "serverless":
        serverless_framework_generator = ServerlessFrameworkGenerator(app_instance)
        serverless_framework_generator.write(save)

    click.echo(
        click.style(f"Done! Generated configuration file saved in {save}", fg="green")
    )


def get_app_instance(file: str) -> Serverless:
    abs_file = os.path.abspath(file)

    if not os.path.exists(abs_file):
        click.echo(
            click.style(
                "The provided file doesn't seem to exist. Please provide a valid python file with -f.",
                fg="red",
            ),
            err=True,
        )
        raise FileNotFoundError

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
        if type(member[1]) == Serverless:
            # Ok. Found the variable now, need to use it
            app_instance = member[1]

    if app_instance is None:  # No variable with type "Serverless" found
        click.echo(
            click.style(
                "Unable to locate an instance of serverless App in the provided file.",
                fg="red",
            ),
            err=True,
        )
        raise ImportError

    return app_instance


def main():
    try:
        return cli()
    except Exception:
        click.echo(traceback.format_exc(), err=True)
        return 2
