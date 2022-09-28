import os
from urllib.parse import urljoin

import requests

SCALEWAY_API_URL = "https://api.scaleway.com/"
TESTS_DIR = os.path.realpath(os.path.dirname(__file__))
APP_PY_PATH = os.path.join(TESTS_DIR, "dev", "app.py")
MULTIPLE_FUNCTIONS_PY_PATH = os.path.join(TESTS_DIR, "dev", "multiple_functions.py")
ROOT_PROJECT_DIR = os.path.join(TESTS_DIR, "..")


def request_scw_api(route: str, method: str = "GET", **kwargs) -> requests.Response:
    req = requests.request(
        method,
        url=urljoin(SCALEWAY_API_URL, route),
        headers={"X-Auth-Token": os.getenv("SCW_SECRET_KEY")},
        **kwargs
    )
    req.raise_for_status()
    return req
