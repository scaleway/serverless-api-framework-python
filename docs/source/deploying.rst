Deploying
=========

After writing your functions, the included CLI tool `scw-serverless` helps test and deploy your application on Scaleway.

Running locally
---------------

You can test your functions locally before deploying with the `dev` command:

.. code-block:: console

    scw-serverless dev app.py

This will start a local Flask server with your functions that will behave similarly to Scaleway Functions.

By default, functions are served by `/name` on port 8080 with the name being the name of the Python function.

You can then use your favorite tools to query the functions:

.. code-block:: console

    # For a function named def handle()...
    curl http://localhost:8080/handle

This command allows you to test your code, but as this test environment is not quite the same as Scaleway Functions,
there might be slight differences when deploying.

Deploy
------

The `deploy` command will deploy your functions directly.

.. code-block:: console

    scw-serverless deploy --help

The command will wait until all functions are deployed and ready to be called. It will also deploy the corresponding triggers.

If you have routed functions, the deploy command will also call your Serverless Gateway to update the routes to your function.
For more information on the Gateway integration, see also :doc:`gateway`.

Dependencies
------------

.. warning:: Native dependencies are not yet handled by the framework.

Currently, dependencies are handled by including a `requirements.txt` file at the root of your project.
Other dependencies management tools such as pipenv or poetry are not yet supported.

Check out the `requirements file reference`_ documentation for more information.

.. _requirements file reference: https://pip.pypa.io/en/stable/reference/requirements-file-format/
