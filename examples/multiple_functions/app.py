from scw_serverless.app import Serverless

app = Serverless("multiple-functions")

import first  # pylint: disable=all # noqa
import second  # noqa
