import subprocess
import tempfile
import time

import requests
from hypothesis import given, provisional
from hypothesis import strategies as st

from scw_serverless.config.route import GatewayRoute, HTTPMethod
from scw_serverless.deploy.gateway.nginx_config import generate_nginx_config

from ...utils import COLD_START_TIMEOUT, DEPLOYED_TEST_FUNCS, requires_nginx

METHODS = [method.value for method in HTTPMethod]


def check_nginx_config(config: str):
    with tempfile.NamedTemporaryFile(mode="wt", encoding="utf-8") as fp:
        fp.write(config)
        fp.flush()
        try:
            subprocess.run(
                args=["nginx", "-t", "-c", fp.name],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            print(config)
            raise e


@requires_nginx
@given(
    path=st.text(),
    methods=st.lists(st.sampled_from(METHODS)),
    target=provisional.urls(),
)
def test_generate_nginx_config_check_single_route(path, methods, target):
    route = GatewayRoute(path=path, methods=methods, target=target)
    try:
        config = generate_nginx_config(routes=[route])
    except ValueError as e:
        print(e)
        return

    check_nginx_config(config)


@requires_nginx
def test_generate_nginx_config_local_nginx():
    """A simple integration test that runs a Nginx server locally.
    Runs against already deployed functions for simplicity.
    """

    routes = []
    for path, url in DEPLOYED_TEST_FUNCS.items():
        # try:
        #     requests.post(url, timeout=COLD_START_TIMEOUT)
        # except requests.exceptions.RequestException as e:
        #     print(e)
        #     pytest.skip(reason=f"target {url} is unresponsive")
        routes.append(
            GatewayRoute(path="/" + path, methods=[HTTPMethod.GET], target=url)
        )

    config = generate_nginx_config(routes=routes)

    with tempfile.NamedTemporaryFile(mode="wt", encoding="utf-8", delete=False) as fp:
        fp.write(config)
        fp.flush()
        with subprocess.Popen(
            args=["nginx", "-c", fp.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ):
            base_url = "http://localhost:8080"
            time.sleep(1)
            for route in routes:
                requests.get(base_url + route.path, timeout=COLD_START_TIMEOUT)
