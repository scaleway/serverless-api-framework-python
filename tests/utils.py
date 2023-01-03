import os

SCALEWAY_API_URL = "https://api.scaleway.com/"
TESTS_DIR = os.path.realpath(os.path.dirname(__file__))
APP_PY_PATH = os.path.join(TESTS_DIR, "dev", "app.py")
MULTIPLE_FUNCTIONS_PY_PATH = os.path.join(TESTS_DIR, "dev", "multiple_functions.py")
ROOT_PROJECT_DIR = os.path.join(TESTS_DIR, "..")
