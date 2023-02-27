import logging
import os

from scw_serverless.app import Serverless

logging.basicConfig(level=logging.INFO)

app = Serverless(
    "multiple-modules",
    secret={
        "SCW_ACCESS_KEY": os.environ["SCW_ACCESS_KEY"],
        "SCW_SECRET_KEY": os.environ["SCW_SECRET_KEY"],
    },
    env={"S3_BUCKET": os.environ["S3_BUCKET"]},
)

import query  # noqa
import upload  # pylint: disable=all # noqa
