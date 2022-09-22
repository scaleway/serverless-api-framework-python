from scw_serverless.app import Serverless

app = Serverless("integration-tests")


@app.func()
def hello_world(event: dict, context: dict):
    return "Hello World!"


@app.func()
def cloud_of_choice(event: dict, context: dict):
    return "The cloud of choice"


@app.func()
def scaleway(event: dict, context: dict):
    return "Scaleway"
