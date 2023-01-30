from jinja2 import Environment, PackageLoader, select_autoescape

from scw_serverless.config.route import GatewayRoute

env = Environment(
    loader=PackageLoader("scw_serverless.deploy.gateway"),
    autoescape=select_autoescape(),
)


def generate_nginx_config(routes: list[GatewayRoute]) -> str:
    """Generates a Nginx reverse-proxy config for the gateway."""
    for route in routes:
        route.validate()

    template = env.get_template("nginx.conf.jinja2")
    return template.render(routes=routes)
