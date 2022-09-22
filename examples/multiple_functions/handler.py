import os

from scw_serverless.app import Serverless

app = Serverless("multiple-functions")


@app.func()
def handle(event, content):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return {"message": "This function is handled by Scaleway functions using Serverless API Framework"}


@app.func(
    description="Say hi",
    privacy="public",
    env={"CUSTOM_NAME": "everyone"},
    secret={"SECRET_VALUE", "***"},
    min_scale=0,
    max_scale=2,
    memory_limit=128,
    timeout="300s",
    custom_domains=["hello.functions.scaleway"],
)
def hello(event, content):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return {"message": f"Hello {os.getenv('CUSTOM_NAME')} from Scaleway functions using Serverless API Framework"}
