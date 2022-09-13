# Function Frameworks Research

This document recaps my research on the different functions framework including Chalice from AWS, Google Functions
Framework, Azure Functions and Dapr.

## Framework overview

### Chalice

Chalice, is the framework which is the easiest to use. You simply write your code add annotations to it and you're done!
In the other hand, Chalice can only be used with AWS Lambdas.

### Google Functions Framework

Google Functions Framework, follow the same idea as Chalice, you have a very basic annotations api that you use to
create functions. The biggest down side is that there is no real documentation and you have to find how to use it by
yourself.
Google Functions Framework uses Flask as its webserver.

### Azure Functions

This is not a real framework. Azure Functions only provide "bindings". For example the one for HTTP only gives you a
request and a response, and you have to implement the logic to manage routing etc...
If you want to correctly work with Azure Functions, you are required to install Visual Studio or VSCode with extensions.

### Dapr

Dapr (made by the Linux Foundation), is similar with Chalice as they both share a relatively identical annotations API.
But in the other hand Dapr is made to be running on Kubernetes and not necessarily on "serverless". In the end it uses
FastAPI, Flask or gRPC to run.

TODO: search about the community why to use theses framework

## Questions

1. What are the similarities between the four APIs?
   > They all use a decorator/annotation API where you define your routes, event handler etc...

2. How do they configure the functions, do they generate configuration files in the background?
   > Every framework other than Google Functions generate configuration in the background.

3. Does the user have to write any configuration files?
   > For Azure Functions, the user is required to write configuration files.  
   > For Chalice, configuration is required if you want to customize the resources usages  
   > For Google Functions Framework there seems to have no configuration file by rather parameters to the CLI.  
   > For Dapr, you have to create configuration to define components.

4. How much of the project is specific to the underlying cloud provider?
   > Chalice is 100% specific to AWS even if you can generate Terraform configuration.  
   > Google Functions Framework can be run on anything that support custom docker images.  
   > Azure Functions is 100% specific to Azure.  
   > Dapr is not specific to any cloud provider. They make it easier for you to run on Azure (with an extension) but you
   can run your app on Kubernetes or a simple virtual machine.

5. Which parts of the API can we adopt in our project?
   > We have two solutions:
   >
   >    1. Create a new framework with its own features.  
           >       In that case the annotation api seems to be more developer-friendly and easier for us to
   >    2. Create an extension flask/fast api to integrate the features we want to facilitate the usage of serverless.
   >
   > In either case, I think we need a powerful CLI (included in the scaleway's CLI or a dedicated one).

    1. Terraform / Serverless Framework config generation
    2. deployment cli
    3. http+events
    4. logging
    5. determine the python version to use when the user execute our cli deployment command

For Flask we can override the App class and intercept decorators calls
For FastAPI we can retrieve the list of routes

The approach of Google Functions Framework is more developer friendly as it relies on Flask for Python, Express for Node
etc... but in another hand it completely replace its API but the framework's one. Maybe a mix between the approach of
GFF and Chalice would do the trick.
