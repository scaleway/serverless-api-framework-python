from typing import Any

from scw_serverless import Serverless

app = Serverless("hello_world")


@app.func()
def handle(_event: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """A simple function deployed using Github Actions."""

    return {
        "message": "Hello from Scaleway functions using"
        + "Serverless API Framework deployed with Github Actions"
    }
