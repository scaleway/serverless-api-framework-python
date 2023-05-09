import os
from pathlib import Path

from scaleway_core.bridge import region

DEFAULT_REGION = region.REGION_PL_WAW
SCALEWAY_API_URL = "https://api.scaleway.com/"
SCALEWAY_FNC_API_URL = SCALEWAY_API_URL + f"functions/v1beta1/regions/{DEFAULT_REGION}"

COLD_START_TIMEOUT = 20

GATEWAY_HOST = os.getenv("GATEWAY_HOST")
GATEWAY_S3_REGION = os.getenv("S3_REGION", str(DEFAULT_REGION))
GATEWAY_S3_BUCKET_ENDPOINT = os.getenv(
    "S3_ENDPOINT", f"https://s3.{DEFAULT_REGION}.scw.cloud"
)
GATEWAY_S3_BUCKET_NAME = os.getenv("GATEWAY_S3_BUCKET_NAME")

TESTS_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_DIR = Path(TESTS_DIR).parent

APP_FIXTURES_PATH = Path(TESTS_DIR, "app_fixtures")

APP_PY_PATH = APP_FIXTURES_PATH / "app.py"
MULTIPLE_FUNCTIONS = APP_FIXTURES_PATH / "multiple_functions.py"
