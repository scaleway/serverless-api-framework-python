from typing import Any

from app import app


@app.func()
def handle(_event: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """A simple function that greets people."""
    return {
        "message": "This function is handled by Scaleway"
        + "functions using Serverless API Framework"
    }
