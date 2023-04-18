Configuring
===========

Namespace
---------

The first step is to create a Serverless instance, which maps to a function namespace. All your functions will be deployed to this namespace.
When deploying, the `scw-serverless` CLI will look for a Serverless instance in the global scope.

.. code-block:: python

   import os
   from scw_serverless import Serverless

   app = Serverless(
      "my-namespace",
      env={
         "NON_CONFIDENTIAL_PARAMETERS": "My Param"
      },
      secret={
         "SCW_SECRET_KEY": os.environ["SCW_SECRET_KEY"],
         "MY_SECRET_KEY": os.environ["MY_SECRET_KEY"]
      },
   })

.. autoclass:: scw_serverless.app.Serverless
   :members: func, get, post, put

Functions
---------

To configure your serverless functions, you can provide keyword arguments to the decorators. The Function name that will appear in the Scaleway console will be the name of your function's handler.

.. autoclass:: scw_serverless.config.function.FunctionKwargs

.. code-block:: python

   app = Serverless("example")
   app.func(
      privacy="public",
      env={"key": "value"},
      secret={"key": "value"},
      min_scale= 0,
      max_scale= 5,
      memory_limit= 256,
      timeout= 300,
      description= "Lores Ipsum",
      http_option= "enabled", # https only
   )
   def handler(event, context):
      # Do Things
      return {"body": "Hello World"}

Triggers
--------

By default, Scaleway Functions are given an HTTP endpoint that can be called to execute your function.
In addition, you can set up additional triggers that will run your function on specific occasions.

Cron triggers
^^^^^^^^^^^^^

To create a function that will run periodically, you can use the `schedule` decorator.
If do not want your function to be publicly available, set the privacy to `private`.

.. code-block:: python

   app.schedule("0 8 * * *", privacy="private")
   def handler(event, context):
      ...

.. autofunction:: scw_serverless.app.Serverless.schedule
