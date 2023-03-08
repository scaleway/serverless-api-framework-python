Serverless API Framework
========================

This framework is designed to make it a breeze to deploy your `Serverless Functions`_ on Scaleway's
infrastructure.

No need for configuration files, the framework makes it possible to configure your functions directly from your code.

.. _Serverless Functions: https://www.scaleway.com/en/serverless-functions/

:doc:`configuring`
    Writing a Serverless app and configuring your functions.

:doc:`deploying`
    Instructions to deploy your project with the CLI tool.

:doc:`gateway`
    Instructions to create an API gateway to manage HTTP routing to functions.

:doc:`examples`
    Examples to get you started.

Quickstart
----------

Installation
^^^^^^^^^^^^

.. code-block:: console

    pip install scw_serverless

This will install `scw-serverless`:

.. code-block:: console

    scw-serverless --help

The tool uses the same configuration_ as the Scaleway CLI to access your account.
This includes the environment variables.

.. _configuration: https://github.com/scaleway/scaleway-sdk-go/tree/master/scw#scaleway-config

Usage
^^^^^

Annotate your Python functions with the `func` decorator:

.. code-block:: python

    from scw_serverless import Serverless

    app = Serverless("hello-namespace")

    @app.func(memory_limit=256)
    def hello_world(event, context):
        return "Hello World!"

Deploy with the `scw-serverless` tool:

.. code-block:: console

    scw-serverless deploy handler.py

To learn more about the different configuration options, check out :doc:`configuring`.

.. Hidden TOC

.. toctree::
   :caption: Contents
   :maxdepth: 2
   :hidden:

   configuring
   deploying
   gateway
   examples
