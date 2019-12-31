from email.message import Message
from email.parser import Parser
from urllib.parse import urlparse, parse_qs

import chardet

from backend.errors import Errors
from backend.logger import Logger


class Request:
    def __init__(self):
        self.method = None
        self.target = None
        self.version = None
        self.headers = {}
        self.file = None
        self.user = None
        self.url = None
        self.path = None
        self.query = None
        self.body = b''

        self._body_to_read = None

        self._multipart = False

        self.filled = False

    def dynamic_fill(self, line: bytes):
        Logger.debug_info(f'Got line {line}')
        if not self._body_to_read:
            if line.endswith(b'\r\n'):
                line = line[:-2]
            elif line.endswith(b'\n'):
                line = line[:-1]

        if not line:
            if not self._multipart:
                header: str = self.headers.get("Content-Type") or ''
                if header.startswith('multipart'):
                    self._multipart = True

            if self._body_to_read == 0:
                self.filled = True
                return True
            if not self._body_to_read:
                length = self.headers.get("Content-Length")
                if length:
                    self._body_to_read = int(length)
                else:
                    self._body_to_read = 0
                    self.filled = True
                    return True
            return False

        if not self.method:
            line = Request.decode(line)
            self.method, self.target, self.version = line.split()
            self.url = urlparse(self.target)
            self.path = self.url.path
            self.query = parse_qs(self.url.query)
            return False

        if self._body_to_read != 0 and self._body_to_read is not None:
            self.body += line
            self._body_to_read -= len(line)
            if self._body_to_read < 0:
                raise Errors.CONTENT_LENGTH_REQUIRED
            if self._body_to_read == 0:
                self.filled = True
                return True
        else:
            p = Parser()
            headers: Message = p.parsestr(Request.decode(line))
            if headers.items():
                for k, v in headers.items():
                    self.headers[k] = v

    def __str__(self):
        return '\n'.join(f'{k}: {v}' for k, v in self.__dict__.items())

    @staticmethod
    def parsed_req_to_request(method, target,
                              ver, headers, body, file, peer=None):
        return Request(method, target, ver, headers, file, peer, body)

    @staticmethod
    def decode(b):
        encoding = chardet.detect(b)['encoding']
        return str(b, encoding or 'utf-8')

    @staticmethod
    def parse_headers_str(s):
        p = Parser()
        return p.parsestr(s)
