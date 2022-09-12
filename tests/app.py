from src.serverless import App

serverlessApp = App("helloworld")


@serverlessApp.func(url="/")
def hello_world(event: dict, context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return "Hello World!"
