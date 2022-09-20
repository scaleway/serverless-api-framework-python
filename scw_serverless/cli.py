import importlib.util
import inspect
import os.path
import traceback

import click

from scw_serverless.app import Serverless
from scw_serverless.config.generators.serverlessframework import (
    ServerlessFrameworkGenerator,
)
from serverless.config.generators.terraform import TerraformGenerator


@click.group()
def cli():
    pass


@cli.command()
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

    click.echo(f"Generating configuration for target: {target}")

    if not os.path.exists(save):
        os.mkdir(save)

    if target == "serverless":
        serverless_framework_generator = ServerlessFrameworkGenerator(app_instance)
        serverless_framework_generator.write(save)
    elif target == "terraform":
        terraform_generator = TerraformGenerator(app_instance)
        terraform_generator.write(save)

    click.echo(
        click.style(f"Done! Generated configuration file saved in {save}", fg="green")
    )


def main():
    try:
        return cli()
    except Exception:
        click.echo(traceback.format_exc(), err=True)
        return 2
