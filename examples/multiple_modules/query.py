import json
import os
from typing import Any

from app import app
from s3 import bucket


@app.func(
    description="List objects in S3 uploads.",
    privacy="public",
    env={"LIMIT": "100"},
    min_scale=0,
    max_scale=2,
    memory_limit=128,
    timeout="300s",
)
def query(_event: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """A handler to list objects in a S3 bucket."""

    response = []

    for obj in bucket.objects.limit(count=int(os.environ["LIMIT"])):
        response.append(
            {
                "name": obj.key,
                "last_modified": obj.last_modified.strftime("%m/%d/%Y, %H:%M:%S"),
                "storage_class": obj.storage_class,
            }
        )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response),
    }
