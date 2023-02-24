import os

import boto3

s3 = boto3.resource(
    "s3",
    region_name="fr-par",
    use_ssl=True,
    endpoint_url="https://s3.fr-par.scw.cloud",
    aws_access_key_id=os.environ["SCW_ACCESS_KEY"],
    aws_secret_access_key=os.environ["SCW_SECRET_KEY"],
)

bucket = s3.Bucket(os.environ["S3_BUCKET"])
