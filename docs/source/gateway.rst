API Gateway
===========

The framework provides support for routed functions via a Gateway container that can be deployed separately.
For more information, please consult the documentation on the `Serverless Gateway repository`_

Quickstart
^^^^^^^^^^

* Write your routed function

.. code-block:: python

   # In app.py

   app = Serverless("example")

   app.get("/hello-gateway", memory_limit= 256)
   def handler(event, context):
      return {"body": "Hello from Gateway!"}

* Clone the `Serverless Gateway repository`_
* Follow the steps in README to deploy your API Gateway
* Create an API token for the Gateway. In the gateway repository, you can use a make command:

.. code-block:: console

    make generate-token
    export TOKEN=$(make get-token)
    export GATEWAY_HOST=$(make gateway-host)

* Finally, use `scw-serverless` to deploy your function and set up the route on your Gateway:

.. code-block:: console

    scw-serverless deploy app.py --gateway-url https://${GATEWAY_HOST} --gateway-api-key ${TOKEN}

* You can now call your function via your Gateway!

.. code-block:: console

    $ curl https://${GATEWAY_HOST}/hello-gateway
    > Hello from Gateway!

.. _Serverless Gateway Repository: https://github.com/scaleway/serverless-gateway
