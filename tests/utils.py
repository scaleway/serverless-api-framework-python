import os
import shutil

import pytest

SCALEWAY_API_URL = "https://api.scaleway.com/"
TESTS_DIR = os.path.realpath(os.path.dirname(__file__))
APP_PY_PATH = os.path.join(TESTS_DIR, "dev", "app.py")
COLD_START_TIMEOUT = 20

requires_nginx = pytest.mark.skipif(
    shutil.which("nginx") is None, reason="nginx must be installed"
)
