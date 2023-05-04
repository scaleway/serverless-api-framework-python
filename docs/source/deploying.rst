Deploying
=========

After writing your functions, the included CLI tool `scw-serverless` helps deploy your application on Scaleway.

Deploy
------

The `deploy` command will deploy your functions directly.

.. code-block:: console

    scw-serverless deploy --help

The command will wait until all functions are deployed and ready to be called. It will also deploy the corresponding triggers.

If you have routed functions, the deploy command will also call your Serverless Gateway to update the routes to your function.
For more information on the Gateway integration, check out :doc:`gateway`.

Dependencies
------------

.. warning:: Native dependencies are not yet handled by the framework.

Currently, dependencies are handled by including a `requirements.txt` file at the root of your project.
Other dependencies management tools such as pipenv or poetry are not yet supported.

Check out the `requirements file reference`_ documentation for more information.

.. _requirements file reference: https://pip.pypa.io/en/stable/reference/requirements-file-format/
