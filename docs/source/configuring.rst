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
      gateway_domains=["app.example.com"]
   })

.. autoclass:: scw_serverless.app.Serverless
   :members: func, schedule, get

Functions
---------

To configure your serverless functions, you can provide keyword arguments to the decorators. The Function name that will appear in Scaleway console will be the name of your the function's handler.

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
      http_option= "enabled" #https only
   )
   def handler(event, context):
      # Do Things
      return {"message": "Hello World"}

Triggers
--------

By default, Scaleway Functions are given an http endpoint that can be called to execute your function.
In addition, you can set up additionnal triggers that will run your function on specific occasions.

Cron triggers
^^^^^^^^^^^^^

.. autoclass:: scw_serverless.triggers.cron.CronTrigger
