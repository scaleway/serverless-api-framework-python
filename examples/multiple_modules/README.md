# [Multiple Modules](https://github.com/scaleway/serverless-api-framework-python/tree/main/examples/multiple_modules)

An app to upload and query files to S3 Glacier on Scaleway split in multiple modules.

The upload endpoint allows you to upload files to Glacier via the `file` form-data key:

```console
echo -e "Hello world!\n My contents will be stored in a bunker!" > myfile.dat
curl -F file=@myfile.dat <upload-function-url>
```

This example is there to showcase how to split handlers into different Python modules.

## Deploying

Deployment can be done with `scw_serverless`:

```console
pip install scw_serverless
scw-serverless deploy app.py
```

## Configuration

Here's all the environments variables that needs to be passed when deploying:

|     Variable     |               Description               |      Required      |
|:----------------:|:---------------------------------------:|:------------------:|
| `SCW_SECRET_KEY` |   Secret key to use for S3 operations   | :heavy_check_mark: |
| `SCW_ACCESS_KEY` |   Access key to use for S3 operations   | :heavy_check_mark: |
|   `S3_BUCKET`    | Name of the bucket to store files into. | :heavy_check_mark: |
