# Serverless API Framework

[![PyPI version](https://badge.fury.io/py/scw-serverless.svg)](https://badge.fury.io/py/scw-serverless)
[![Documentation Status](https://readthedocs.org/projects/serverless-api-project/badge/?version=latest)](https://serverless-api-project.readthedocs.io/en/latest/?badge=latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/scaleway/serverless-api-framework-python/main.svg)](https://results.pre-commit.ci/latest/github/scaleway/serverless-api-framework-python/main)

Serverless API Framework is a tool that lets you write and deploy serverless functions in Python.
It bridges your code with the deployment configuration to make it a breeze to work with serverless functions.

Starts by defining a simple Python function:

```python
from scw_serverless import Serverless

app = Serverless("hello-namespace")

@app.func(memory_limit=256)
def hello_world(event, context):
    return "Hello World!"
```

Deploy it with `scw-serverless`:

```console
scw-serverless deploy app.py
```

## Quickstart

### Install

```console
pip install scw-serverless
```

This will install the `scw-serverless` CLI:

```console
scw-serverless --help
```

### Writing and configuring functions

You can transform your Python functions into serverless functions by using decorators:

```python
import os
import requests
from scw_serverless import Serverless

app = Serverless("hello-namespace")
API_URL = os.environ["API_URL"]

@app.func(memory_limit=256, env={"API_URL": API_URL})
def hello_world(event, context):
    return requests.get(API_URL)
```

The configuration is done by passing arguments to the decorator.
To view which arguments are supported, head over to this [documentation](https://serverless-api-framework-python.readthedocs.io/) page.

### Local testing

Before deploying, you can run your functions locally with the dev command:

```console
scw-serverless dev app.py
```

This runs a local Flask server with your Serverless handlers. If no `relative_url` is defined for a function, it will be served on `/name` with `name` being the name of your Python function.

By default, this runs Flask in debug mode which includes hot-reloading. You can disable this behavior by passing the `--no-debug` flag.

### Deploying

When you are ready, you can deploy your function with the `scw-serverless` CLI tool:

```console
scw-serverless deploy app.py
```

The tool will use your Scaleway credentials from your environment and config file.

## What’s Next?

To learn more about the framework, have a look at the [documentation](https://serverless-api-project.readthedocs.io/).
If you want to see it in action, we provide some [examples](https://github.com/scaleway/serverless-api-framework-python-python/tree/main/examples) to get you started.

To run your Python functions locally, check out [Scaleway Functions Python](https://github.com/scaleway/serverless-functions-python).

## Contributing

We welcome all contributions.

This project uses [pre-commit](https://pre-commit.com/) hooks to run code quality checks locally. We recommended installing them before contributing.

```console
pre-commit install
```
