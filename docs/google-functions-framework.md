# Framework functions

Mainly made to build docker image with custom Dockerfiles to be then run on gcp.

- How do they configure functions, do they generate configuration files in the background?
    - Decorator API
    - Not at first glance

- Do the user have to write any configuration files?
    - NO

- How much of the project is specific to the underlying cloud provider?
    - Can be run on Knative and Google Cloud Functions + You can build a docker image
    - deployment is made with a separate tool `gcloud`

- Which parts of the API can we adopt in our project?

## Random things

Uses layers: google.python.runtime:python, google.python.functions-framework:functions-framework and google.python.pip:
pip

## Pros

Seems to be usable on every cloud providers supporting containers.
Uses Flask internally (Maybe there is a way to use it)

## Cons

Very poor documentation
