from typing import Any

from scw_serverless.app import Serverless

app = Serverless("integration-tests")


@app.func(
    description="This is a description",
    privacy="public",
    env={"key": "value"},
    secret={},
    min_scale=0,
    max_scale=20,
    memory_limit=256,
    timeout="300s",
)
def hello_world(_event: dict[str, Any], _context: dict[str, Any]):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return "Hello World!"
