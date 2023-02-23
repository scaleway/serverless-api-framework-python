import os
from typing import Any

from app import app


@app.func(
    description="Happy Coding!",
    privacy="public",
    env={"CUSTOM_NAME": "everyone"},
    secret={"SECRET_VALUE": "***"},
    min_scale=0,
    max_scale=2,
    memory_limit=128,
    timeout="300s",
)
def hello(_event: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """A simple function that greets people."""
    return {
        "message": f"Hello {os.getenv('CUSTOM_NAME')}"
        + "from Scaleway functions using Serverless API Framework"
    }
