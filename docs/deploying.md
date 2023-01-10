# Deploying

After writing your functions, the included CLI tool `srvless` helps deploy your application on Scaleway.

## Deploy

The `deploy` command will deploy your functions directly.

```console
srvless deploy --help
```

The command will wait until all functions are deployed and ready to be called. It will also deploy the corresponding triggers.

## Generators

Generators will generate configuration files to use with other deployment tools. Currently, you can generate either a `serverless` or `terraform` configuration file. This can useful to integrate with your existing tooling.

Config file generation is done with the `generate` command:

```console
srvless generate -b serverless
```

```{eval-rst}
.. autoclass:: scw_serverless.config.generators.ServerlessFrameworkGenerator
```

```{eval-rst}
.. autoclass:: scw_serverless.config.generators.TerraformGenerator
```

## Dependencies

```{warning} Native dependencies are not yet handled by the framework.
```

Currently, dependencies are handled by including a `requirements.txt` file at the root of your project.
Other dependencies management tools such as pipenv or poetry are not yet supported.

See: <https://pip.pypa.io/en/stable/reference/requirements-file-format/> for more information on the requirements file format.
