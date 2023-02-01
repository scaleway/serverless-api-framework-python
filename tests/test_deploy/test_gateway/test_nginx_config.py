import shutil
import string
import subprocess
import tempfile
from pathlib import Path

import pytest
from hypothesis import example, given, provisional
from hypothesis import strategies as st

from scw_serverless.config.route import GatewayRoute, HTTPMethod
from scw_serverless.deploy.gateway.nginx_config import generate_nginx_config

from ...utils import TESTS_DIR, requires_nginx

PATH_STRATEGY = st.lists(
    st.text(alphabet=string.ascii_lowercase, min_size=1), max_size=20
)
ROUTE_STRATEGY = st.builds(
    GatewayRoute,
    path=st.builds("/".join, PATH_STRATEGY),
    methods=st.lists(
        st.builds(HTTPMethod, st.sampled_from(list(HTTPMethod))), unique=True
    ),
    target=provisional.urls(),
)
TEST_TARGET = "https://scaleway.com"


# pylint: disable=redefined-outer-name # fixture
@pytest.fixture(scope="session")
def helpers_temp_dir():
    helpers_dir = Path(TESTS_DIR).parent.joinpath("deploying/gateway/helpers")
    with tempfile.TemporaryDirectory() as tmp_dir:
        shutil.copytree(helpers_dir, tmp_dir, dirs_exist_ok=True)
        yield tmp_dir


def check_nginx_config(config: str):
    with tempfile.NamedTemporaryFile(mode="wt", encoding="utf-8", delete=False) as fp:
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
            print(e.stderr)
            print(config)
            raise e


@requires_nginx
@given(routes=st.lists(ROUTE_STRATEGY, max_size=20))
# Example where methods are None
@example(routes=[GatewayRoute("/", None, TEST_TARGET)])
# Example with a route that contains a "-"
@example(
    routes=[
        GatewayRoute("/messages", [HTTPMethod.GET], TEST_TARGET),
        GatewayRoute("/messages", [HTTPMethod.POST], TEST_TARGET),
        GatewayRoute(
            "/messages/by-length/", [HTTPMethod.GET, HTTPMethod.PUT], TEST_TARGET
        ),
    ]
)
def test_generate_nginx_config_check(routes: list[GatewayRoute], helpers_temp_dir: str):
    try:
        config = generate_nginx_config(routes=routes)
    except ValueError as e:
        print(e)
        return

    # We running it locally, the helpers must
    config = config.replace("/etc/nginx/helpers", helpers_temp_dir)
    check_nginx_config(config)
