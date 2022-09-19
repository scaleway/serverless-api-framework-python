from serverless.app import Serverless
from serverless.events.cron import Cron

app = Serverless("helloworld", env={"key1": "value1"}, secret={"key2": "value2"})


@app.func(
    description="This is a description",
    privacy="public",
    env={"key": "value"},
    secret={},
    min_scale=0,
    max_scale=20,
    memory_limit=128,
    timeout=300,
    custom_domains=["domain.scw.cloud"],
)
def hello_world(event: dict, context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return "Hello World!"

@app.schedule(
    schedule=Cron("1", "*", "*", "*", "*", "*"),
    inputs={"my_name": "Georges"},
    description="This is a description",
    privacy="public",
    env={"key": "value"},
    custom_domains=["domain.scw.cloud"],
)
def hello_world_cron(event: dict, _context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """
    return f'Hello {event["my_name"]}!'