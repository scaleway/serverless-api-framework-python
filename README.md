# Serverless API Framework

Serverless API Framework is a tool that lets you write and deploy serverless functions in python.
It bridges your code with the deployment configuration to make it a breeze to work with serverless functions.

Starts by defining a simple Python function:

```python
from scw_serverless import Serverless

app = Serverless("hello-namespace")

@app.func(memory_limit=256)
def hello_world(event, context):
    return "Hello World!"
```

Deploy it with `scw_serverless`:

```console
srvless deploy app.py
```

## Quickstart

### Install

```console
pip install scw_serverless
```

This will install `srvless`:

```console
srvless --help
```

### Writing and configuring functions

You can transform your python functions into serverless functions by using decorators:

```python
import os
import requests
from scw_serverless import Serverless

app = Serverless("hello-namespace")

@app.func(memory_limit=256, env={"API_URL": os.environ["API_URL"]})
def hello_world(event, context):
    requests.get("")
```

The configuration is done by passing arguments to the decorator.
To view which arguments are supported, head over to this [documentation]() page.

When you are ready, you can deploy your function with the `srvless` CLI tool:

```console
srvless deploy app.py
```

The tool will use your Scaleway credentials from your environment and config file.

## What’s Next?

To learn more about the framework, have a look at the [documentation]().
If you want to see it action, we provide some [examples]() to get you started.

## Contributing

We welcome all contributions.

This project uses [pre-commit](https://pre-commit.com/) hooks to run code quality checks locally. We recommended installing them before contributing.

```console
pre-commit install
```
