from enum import IntEnum


class HttpStatusCode(IntEnum):
    OK = 200
    BAD_REQUEST = 400
    NO_CONTENT = 204
    NOT_FOUND = 404
