import click

from tests.app import app


@click.group()
def cli():
    pass


@cli.command()
@click.option("--target", "-t", "target", default="serverless",
              type=click.Choice(["serverless"], case_sensitive=False))
def generate(target):
    click.echo(f"Generating configuration for target: {target}")

    app.write_serverless_framework_yaml()

    click.echo(click.style('Done!', fg='green'))


if __name__ == '__main__':
    cli()
