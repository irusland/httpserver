import json
import re
import tempfile
from email.message import Message
from email.parser import Parser
from urllib.parse import urlparse, parse_qs

import chardet

from ihttpy.exceptions.logger import Logger


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

        self.body_file = tempfile.TemporaryFile(mode='w+b')

        self._body_to_read = None

        self._multipart = False

        self.filled = False

    def dynamic_fill(self, line: bytes):
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
                    if self._body_to_read == 0:
                        self.filled = True
                        return True
                else:
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
            self.body_file.write(line)
            self._body_to_read -= len(line)
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
    def decode(b):
        encoding = chardet.detect(b)['encoding']
        return str(b, encoding or 'utf-8')

    @staticmethod
    def parse_headers_str(s):
        p = Parser()
        return p.parsestr(s)

    def insufficient(self):
        return not self.method or not self.path or not self.version

    @staticmethod
    def split_keep_sep(s: bytes, sep):
        xs = re.split(rb'(%s)' % re.escape(sep), s)
        if xs[-1] == b'':
            del xs[-1]
        return [xs[i] + (xs[i + 1] if i + 1 < len(xs) else b'')
                for i in range(0, len(xs), 2)]

    @staticmethod
    def fill_from_line(line):
        r = Request()
        split = Request.split_keep_sep(line, b'\r\n')
        for s in split:
            if r.dynamic_fill(s):
                return r

    def get_json(self):
        self.body_file.seek(0)
        body = self.body_file.read()
        body = Request.decode(body)
        Logger.debug_info(f'PUT -> {body}')
        return json.loads(body)
