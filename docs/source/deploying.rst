Deploying
=========

After writing your functions, the included CLI tool `srvless` helps deploy your application on Scaleway.

Deploy
------

The `deploy` command will deploy your functions directly.

.. code-block:: console

    srvless deploy --help

The command will wait until all functions are deployed and ready to be called. It will also deploy the corresponding triggers.

Generate
--------

Generators will generate configuration files to use with other deployment tools.
Currently, you can generate either a `serverless` or `terraform` configuration file. This can useful to integrate with your existing tooling.

Config file generation is done with the `generate` command:

.. code-block:: console

    srvless generate -b serverless

Serverless Generator
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: scw_serverless.config.generators.ServerlessFrameworkGenerator

Terraform Generator
^^^^^^^^^^^^^^^^^^^

.. autoclass:: scw_serverless.config.generators.TerraformGenerator

Dependencies
------------

.. warning:: Native dependencies are not yet handled by the framework.

Currently, dependencies are handled by including a `requirements.txt` file at the root of your project.
Other dependencies management tools such as pipenv or poetry are not yet supported.

Check out the `requirements file reference`_ documentation for more information.

.. _requirements file reference: https://pip.pypa.io/en/stable/reference/requirements-file-format/
