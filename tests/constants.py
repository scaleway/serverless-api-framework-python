import os
from pathlib import Path

from scaleway_core.bridge.region import REGION_FR_PAR

DEFAULT_REGION = REGION_FR_PAR
SCALEWAY_API_URL = "https://api.scaleway.com/"
SCALEWAY_FNC_API_URL = SCALEWAY_API_URL + f"functions/v1beta1/regions/{DEFAULT_REGION}"

COLD_START_TIMEOUT = 20

TESTS_DIR = os.path.realpath(os.path.dirname(__file__))

APP_FIXTURES_PATH = Path(TESTS_DIR, "app_fixtures")

APP_PY_PATH = APP_FIXTURES_PATH / "app.py"
MULTIPLE_FUNCTIONS = APP_FIXTURES_PATH / "multiple_functions.py"
