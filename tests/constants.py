import os
from pathlib import Path

DEFAULT_REGION = "fr-par"
SCALEWAY_API_URL = "https://api.scaleway.com/"

COLD_START_TIMEOUT = 20

TESTS_DIR = os.path.realpath(os.path.dirname(__file__))

APP_FIXTURES_PATH = Path(TESTS_DIR, "app_fixtures")

APP_PY_PATH = APP_FIXTURES_PATH / "app.py"
MULTIPLE_FUNCTIONS = APP_FIXTURES_PATH / "multiple_functions.py"
