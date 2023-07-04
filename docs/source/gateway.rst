API Gateway
===========

The framework provides support for routed functions via the Serverless Gateway project that can be deployed separately.
For more information, please consult the documentation on the `Serverless Gateway repository`_

Quickstart
^^^^^^^^^^

* Write your routed function

.. code-block:: python

   # In app.py

   app = Serverless("example")

   # You can use the get, post, put, and delete decorators
   @app.get("/hello-gateway", memory_limit= 256)
   def handler(event, context):
      return {"body": "Hello from Gateway!"}

* Install the `scwgw` helper tool

.. code-block:: console

    pip install scw-gateway

* Deploy your API Gateway

.. code-block:: console

    scwgw infra deploy

* Finally, use `scw-serverless` to deploy your function and set up the route on your gateway:

.. code-block:: console

    scw-serverless deploy app.py

* You can now call your function via your Gateway!

.. code-block:: console

    $ GATEWAY_ENDPOINT=$(scwgw infra endpoint)
    $ curl https://${GATEWAY_ENDPOINT}/hello-gateway
    > Hello from Gateway!

.. _Serverless Gateway Repository: https://github.com/scaleway/serverless-gateway
