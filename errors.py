import json

from defenitions import CONFIG_PATH


class Error(Exception):
    def __init__(self, status, reason, body=None, page=None):
        self.status = status
        self.reason = reason
        self.body = body
        if page:
            with open(CONFIG_PATH) as cfg:
                data = json.load(cfg)
                self.page = data["error-pages"][page]


class Errors(Error):
    REQ_TOO_LONG = Error(400, 'Bad request',
                         'Request line is too long')
    MALFORMED_REQ = Error(400, 'Bad request',
                          'Malformed request line')
    HEADER_MISSING = Error(400, 'Bad request',
                           'Host header is missing')
    NOT_FOUND = Error(404, 'Not found', "", "PAGE_NOT_FOUND")
    HEADER_TOO_LARGE = Error(494, 'Request header too large')
    TOO_MANY_HEADERS = Error(494, 'Too many headers')
    VERSION_NOT_SUPPORTED = Error(505, 'HTTP Version Not Supported')