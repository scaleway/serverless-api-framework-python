from typing import Any

from scw_serverless.app import Serverless

app = Serverless("hello_world")


@app.func()
def handle(_event: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return {
        "message": "Hello from Scaleway functions using"
        + "Serverless API Framework deployed with Github Actions"
    }
