from serverless.app import Serverless

app = Serverless("helloworld", env={"key1": "value1"}, secret={"key2": "value2"})


@app.func(
    description="This is a description",
    privacy="public",
    env={"key": "value"},
    secret={},
    min_scale=0,
    max_scale=20,
    memory_limit=128,
    timeout="300s",
    custom_domains=["domain.scw.cloud"],
)
def hello_world(event: dict, context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return "Hello World!"
