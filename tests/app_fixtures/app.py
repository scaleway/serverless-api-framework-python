from typing import Any

from scw_serverless.app import Serverless

DESCRIPTION = "Say hello to the whole world."
MESSAGE = "Hello World!"
NAMESPACE_NAME = "integration-tests"

app = Serverless(NAMESPACE_NAME)


@app.func(
    description=DESCRIPTION,
    privacy="public",
    env={"key": "value"},
    secret={},
    min_scale=0,
    max_scale=20,
    memory_limit=256,
    timeout="300s",
)
def hello_world(_event: dict[str, Any], _context: dict[str, Any]):
    return MESSAGE
