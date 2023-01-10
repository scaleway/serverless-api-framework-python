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

## Triggers

By default, Scaleway Functions are given an http endpoint that can be called to execute your function.
In addition, you can set up additionnal triggers that will run your function on specific occasions.

### Cron triggers

```{eval-rst}
.. autoclass:: scw_serverless.triggers.cron.CronTrigger
```
