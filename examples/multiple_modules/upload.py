import logging
from typing import Any

from app import app
from s3 import bucket
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget


@app.func()
def upload(event: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """Upload form data to S3 Glacier."""

    headers = event["headers"]
    parser = StreamingFormDataParser(headers=headers)

    target = ValueTarget()
    parser.register("file", target)

    body: str = event["body"]
    parser.data_received(body.encode("utf-8"))

    if not (len(target.value) > 0 and target.multipart_filename):
        return {"statusCode": 400}

    name = target.multipart_filename

    logging.info("Uploading file %s to Glacier on %s", name, bucket.name)
    bucket.put_object(Key=name, Body=target.value, StorageClass="GLACIER")

    return {"statusCode": 200}
