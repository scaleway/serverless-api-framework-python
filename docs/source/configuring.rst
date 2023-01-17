Configuring
===========

Namespace
---------

The first step is to create a Serverless instance, which maps to a function namespace.
When deploying, the `scw-serverless` CLI will look for a Serverless instance in the global scope.

.. code-block:: python

   import os
   from scw_serverless import Serverless

   app = Serverless("my-namespace", secret={
      "SCW_SECRET_KEY": os.environ["SCW_SECRET_KEY"]
   })

.. autoclass:: scw_serverless.app.Serverless
   :members: func, schedule, get

Functions
---------

To configure your serverless functions, you can provide keyword arguments to the decorators.

.. autoclass:: scw_serverless.config.function.FunctionKwargs

Triggers
--------

By default, Scaleway Functions are given an http endpoint that can be called to execute your function.
In addition, you can set up additionnal triggers that will run your function on specific occasions.

Cron triggers
^^^^^^^^^^^^^

.. autoclass:: scw_serverless.triggers.cron.CronTrigger
