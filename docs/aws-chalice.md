# Chalice

- Pros of Chalice
    - Easy to use
    - Lightweight for deployment + 2k lines added. what runtime do they use ?

- Cons of Chalice
    - Specific to AWS, it uses all the aws serverless environment, and there is nothing at first glance that allow us to
      not use it in the end.
    - Everything is specific to AWS, backend, configuration generation etc...

- How do you configure functions, does chalice generate configuration file in the background ?
    - Apart for the initial chalice configuration generated with the `chalice new-project helloworld` it seems like
      there is no more configuration needed
    - When packaging the app to terraform, there is no configuration generated apart from the tf.json file for terraform
      which is specific to aws
    - To configure function you annotate your code with `route`, `on_s3_event`, `on_sns_message`, `on_sqs_message`
      , `on_cw_event`, `on_kinesis_record`, `on_dynamodb_record` and `lambda_functions` which are specific to aws
      and `schedule`for CRONs.

- Does the user have to write any configuration files ?
    - No

- How much of the project is specific to AWS ?
    - Everything

- Which part of the API can we adopt in our project ?
    - Support for HTTP, and external events (as mentioned above)
    - decorator api, easy to use

Chalice is not limited to single file. everything under the `chalicelib` directory is automatically imported python file
or not.

> In each project, a .chalice folder with the configuration is created. When deployed a deployed folder with json files
> corresponding to the environnement we just deployed to is created. In this config file, there is the list of resources
> attached to that deployment including: the lambda function, the iam role and the api gateway

## CLI

In order to work, user have to configure their aws credentials. There is no interactive way of doing it. Don't know yet
for environment variable (useful for CI/CD)

- new-project: Initialize a new project with the default configuration files
- deploy: deploy to AWS (takes 20s)
- delete: delete all attached resources from aws (takes 2s)

## Routing

No "Request" object is passed to the function, to retrieve the request we need to use `app.current_request`. I feel like
this is not very user friendly especially yo only retrieve query params

The only values provided to the function are path parameters

You can return a Response object everything else is serialized to json. (Maybe we want a default behavior for non
objects/list ?)


 ```python
 @app.route(
  '/resource uri', # Resource route
  methods=['GET', 'POST', ...], # List of valid HTTP verbs
  content_type=['text/plain'], # List of accepted content_type. 415 if not in the list. Accept and Content-Type header are required in the request, otherwise -> 400 Bad Request
  authorizer=None # Authorizer function. see: https://aws.github.io/chalice/topics/authorizers.html
)
 ```

Multiple function can share the same route by with different methods

## Event Sources

- schedule: Take a Rate or Cron parameter
- cloud watch
- s3
- sns
- sqs
- kinesis
- dynamoDB

## Error handling

Made through the use of exception, a few one are provided by default

## Configuration

As mentioned a .chalice folder is created with the configuration files.
**Chalice is not 100% configuration free** you have to edit config files for your ram settings (for example).

There is the ability to create different configuration depending on the stage.

### Important settings

some settings are ignored if too specific for aws (see: <https://aws.github.io/chalice/topics/configfile.html>)

- environment_variables: K/V (only string) set as environment variables
- lambda_memory_size: amount in MB to give to your function. CPU is inferred from this value. Default: 128. Must be a
  multiple of 64
- lambda_timeout: the function timeout in seconds. Default: 60
- api_gateway_custom_domain:
    - domain_name: ex: api.scw.cloud
    - certificate_arn: (No idea what this is, maybe an id to a previously created certificate)
      optionally:
        - tls_version
        - url_prefix: ex: api.scw.cloud/my_url_prefix
        - tags
- websocket_api_custom_domain: same as api_gateway_custom_domain
- reserved_concurrency: max number of concurrent execution. min: 0 = invocation blocked

Some settings can be per lambda function, but still in the same configuration files

## Other "random things"

### Logging

Calling `app.log.debug(...` with record log and be accessible with the logs command.
can set the logging level with `app.log.setLevel(logging.DEBUG)`

the `chalice logs` command allow you to give a function name to only retrieve the logs corresponding to a specific
function.

### SDK generation

you can generate an sdk from the project with `chalice generate-sdk` *js only*

### deploy environment

yu can specify the deploy environment directly in the cli with: `chalice deploy --stage dev|prod`

### Python runtime version

version is the same as used during the `chalice deploy`
