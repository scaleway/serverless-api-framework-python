from typing import Any

from scw_serverless import Serverless

app = Serverless("cron", env={"key1": "value1"}, secret={"key2": "value2"})


@app.schedule(
    schedule="0 0 * * MON",
    inputs={"my_name": "Georges"},
    description="This is a description",
    privacy="public",
    env={"key": "value"},
)
def hello_world_cron(event: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """
    return f'Hello {event["my_name"]}!'
