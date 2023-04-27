from typing import Any

from scw_serverless.app import Serverless

app = Serverless("hello-world")


@app.func()
def handle(_event: dict[str, Any], _content: dict[str, Any]) -> dict[str, Any]:
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return {"body": "Hello from Scaleway functions using Serverless API Framework"}
