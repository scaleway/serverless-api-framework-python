# Scaleway Serverless Python API

Serverless API Project is a python framework that let you write serverless apps in python.

You can create a simple function:

```python
from scw_serverless.app import Serverless

app = Serverless("my_service_name")


@app.func()
def hello_world(event: dict, context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return "Hello World!"
```

# Quickstart

Initiate your python environment:

```shell
python3 -m venv venv310
. venv310/bin/activate
```

Install `serverless-api-project`

```shell
python -m pip install scw-serverless-api-project
```

You can then now, create a python file and start coding using the example above.

When you are ready, you can generate a `serverless.yml` configuration file using:

```shell
srvlss generate --file app.py
```
