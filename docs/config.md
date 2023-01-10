# Configuring

The first step is to create a Serverless instance, which maps to a function namespace.
When deploying, the `srvless` CLI will look for a Serverless instance in the global scope.

```{eval-rst}
.. autoclass:: scw_serverless.app.Serverless
   :members: func, schedule, get
```

To configure your serverless functions, you can provide keyword arguments to the decorators.

```{eval-rst}
.. autoclass:: scw_serverless.config.function.FunctionKwargs
```
