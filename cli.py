import importlib.util
import inspect
import os.path

import click

from src.config.generators.serverlessframework import ServerlessFrameworkGenerator
from src.serverless import App


@click.group()
def cli():
    pass


@cli.command()
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
    default="./tests/app.py",
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
    if not os.path.exists(file):
        click.echo(
            click.style(
                "The provided file doesn't seem to exist. Please provide a valid python file with -f.",
                fg="red",
            ),
            err=True,
        )
        raise FileNotFoundError

    module_name = os.path.basename(file)
    module_name = module_name.split(".")[0]

    spec = importlib.util.spec_from_file_location(module_name, file)
    user_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_app)

    app_instance = None

    for member in inspect.getmembers(user_app):
        if type(member[1]) == App:
            # Ok. Found the variable now, need to use it
            app_instance = member[1]

    if app_instance is None:
        click.echo(
            click.style(
                "Unable to locate an instance of serverless App in the provided file.",
                fg="red",
            ),
            err=True,
        )
        raise ImportError

    click.echo(f"Generating configuration for target: {target}")

    if target == "serverless":
        serverless_framework_generator = ServerlessFrameworkGenerator(app_instance)
        serverless_framework_generator.write(save)

    click.echo(
        click.style(f"Done! Generated configuration file saved in {save}", fg="green")
    )


if __name__ == "__main__":
    cli()
