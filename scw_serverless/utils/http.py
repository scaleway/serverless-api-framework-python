from enum import Enum


class HTTPMethod(Enum):
    """Enum of supported HTTP methods.

    See also: https://docs.python.org/3/library/http.html#http.HTTPMethod
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
