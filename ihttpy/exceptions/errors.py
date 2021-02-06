class Error(Exception):
    def __init__(self, status, reason, body=None, page=None):
        self.status = status
        self.reason = reason
        self.body = body
        self.page = page


class Errors(Error):
    REQ_TOO_LONG = Error(400, 'Bad request',
                         'Request line is too long')
    MALFORMED_REQ = Error(400, 'Bad request',
                          'Malformed request line')
    HEADER_MISSING = Error(400, 'Bad request',
                           'Host header is missing')
    NOT_FOUND = Error(404, 'Not found', page="PAGE_NOT_FOUND")
    HEADER_TOO_LARGE = Error(494, 'Request header too large')
    TOO_MANY_HEADERS = Error(494, 'Too many headers')
    VERSION_NOT_SUPPORTED = Error(505, 'HTTP Version Not Supported')
    NO_HANDLER = Error(500, 'No handler for this page found')
    METHOD_NOT_SUPPORTED = Error(500, 'HTTP method not supported')
    CONTENT_LENGTH_REQUIRED = Error(411, 'Proper Content-Length header '
                                         'required')


class KeepAliveExpire(Exception):
    pass
