from typing import Any

from scw_serverless.app import Serverless

MESSAGE = "Hello galaxy!"
DESCRIPTION = "Say hello to the whole galaxy."

app = Serverless("integration-tests")


@app.func(
    description=DESCRIPTION,
    privacy="public",
    env={"key": "value"},
    secret={},
    min_scale=0,
    max_scale=10,  # Differs from app.py
    memory_limit=256,
    timeout="300s",
)
def hello_world(_event: dict[str, Any], _context: dict[str, Any]):
    return MESSAGE
