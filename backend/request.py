from email.parser import Parser
from urllib.parse import urlparse, parse_qs

import chardet


class Request:
    def __init__(self, method, target, version, headers, file, user):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.file = file
        self.user = user
        self.url = urlparse(self.target)
        self.path = self.url.path
        self.query = parse_qs(self.url.query)

    def __str__(self):
        return '\n'.join(f'{k}: {v}' for k, v in self.__dict__.items())

    @staticmethod
    def parsed_req_to_request(method, target,
                              ver, headers, file, peer=None):
        return Request(method, target, ver, headers, file, peer)

    @staticmethod
    def decode(b):
        encoding = chardet.detect(b)['encoding']
        return str(b, encoding or 'utf-8')

    @staticmethod
    def parse_headers_str(s):
        p = Parser()
        return p.parsestr(s)
