# python3

import json
import socket

from email.parser import Parser
from urllib.parse import parse_qs, urlparse

from defenitions import CONFIG_PATH
from ruler import Ruler

import magic


class Server:
    MAX_LINE = 64 * 1024
    MAX_HEADERS = 100

    def __init__(self, host, port, server_name, debug=False):
        self._host = host
        self._port = port
        self._server_name = server_name
        self._list = {}
        self._log = debug
        self.ruler = Ruler()

        # TODO Transfer to Error class as static props
        self.REQ_TOO_LONG_ERR = Error(400, 'Bad request',
                                      'Request line is too long')
        self.MALFORMED_REQ_ERR = Error(400, 'Bad request',
                                       'Malformed request line')
        self.HEADER_MISSING_ERR = Error(400, 'Bad request',
                                        'Host header is missing')
        self.NOT_FOUND_ERR = Error(404, 'Not found')
        self.HEADER_TOO_LARGE_ERR = Error(494, 'Request header too large')
        self.TOO_MANY_HEADERS_ERR = Error(494, 'Too many headers')
        self.VERSION_NOT_SUPPORTED_ERR = Error(505,
                                               'HTTP Version Not Supported')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO Exception handling from serve_client
        # TODO Ask about zombie lasting threads
        self.log(exc_type, exc_val, exc_tb)
        pass

    def log(self, *args):
        if self._log:
            print(args)

    def serve(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self._host, self._port))
        sock.listen()
        print('debug', 'server is UP on 0.0.0.0:8000')

        while True:
            connection, ip = sock.accept()
            self.log(f'New client {ip}')
            self.serve_client(connection)

    def serve_client(self, connection):
        try:
            req = self.parse_req(connection)
            self.log(f'Got request from {req.user} {req}')
            res = self.handle_req(req)
            self.log(f'Response {res}')
            self.send_response(connection, res)
        except Exception as e:
            self.send_error(connection, e)

        connection.close()

    def send_error(self, connection, err):
        try:
            res = self.build_err_res(err.status, err.reason,
                                     (err.body or err.reason).encode('utf-8'))
        except AttributeError as e:
            res = self.build_err_res(500, b'Internal Server Error',
                                     b'Internal Server Error')
        self.send_response(connection, res)

    @staticmethod
    def build_err_res(status, reason, body):
        return Response(status, reason, [('Content-Length', len(body))], body)

    def parse_req(self, connection):
        with connection.makefile('rb') as file:
            method, target, ver = self.parse_request_line(file)
            headers = self.parse_headers(file)
            host = headers.get('Host')
            if not host:
                raise self.HEADER_MISSING_ERR
            if host not in (self._server_name,
                            f'{self._server_name}:{self._port}'):
                raise self.NOT_FOUND_ERR
        return Request(method, target, ver, headers, file,
                       connection.getpeername())

    def parse_request_line(self, reqfile):
        raw = reqfile.readline(self.MAX_LINE + 1)
        if len(raw) > self.MAX_LINE:
            raise self.REQ_TOO_LONG_ERR

        req_line = str(raw, 'utf-8')
        words = req_line.split()
        print('debug', words)
        if len(words) != 3:
            raise self.MALFORMED_REQ_ERR

        method, target, ver = words
        if ver != 'HTTP/1.1':
            raise self.VERSION_NOT_SUPPORTED_ERR
        return method, target, ver

    def parse_headers(self, rfile):
        headers = []
        breakline = [b'\r\n', b'\n', b'']

        while True:
            line = rfile.readline(self.MAX_LINE + 1)
            if len(line) > self.MAX_LINE:
                raise self.HEADER_TOO_LARGE_ERR
            if line in breakline:
                break
            headers.append(line)
            if len(headers) > self.MAX_HEADERS:
                raise self.TOO_MANY_HEADERS_ERR

        return self.parse_headers_str(b''.join(headers).decode('utf-8'))

    @staticmethod
    def parse_headers_str(s):
        p = Parser()
        return p.parsestr(s)

    def handle_req(self, req):
        if req.path.startswith('/') and req.method == 'GET':
            rules = self.ruler.get_rules()
            try:
                destination = self.ruler.get_destination(req.path, rules, True)
            except FileNotFoundError:
                raise self.NOT_FOUND_ERR
            if destination:
                mime = magic.Magic(mime=True)
                content_type = mime.from_file(destination)
                return self.send_file(req, destination, content_type)
        raise self.NOT_FOUND_ERR

    def send_file(self, req, path, content_type):
        accept = req.headers.get('Accept')
        if content_type in accept or '*/*' in accept:
            with open(path, 'rb') as file:
                body = file.read()
        else:
            return Response(406, 'Not Acceptable')

        # body = body.encode('utf-8')
        headers = [('Content-Type', content_type),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)

    def clear_text(self):
        self._list.clear()
        return Response(204, f'Cleared')

    def add_text(self, req):
        id = len(self._list) + 1
        self._list[id] = req.query['text'][0]
        textres = f'<html><head></head><body> Text added ' \
                  f'{req.query["text"][0]}</body></html>'
        body = textres.encode('utf-8')
        content_type = 'text/html; charset=utf-8'
        headers = [('Content-Type', content_type),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)

    def show_text(self, req):
        accept = req.headers.get('Accept')
        if 'text/html' in accept:
            content_type = 'text/html; charset=utf-8'
            body = self.get_html()

        elif 'application/json' in accept:
            content_type = 'application/json; charset=utf-8'
            body = json.dumps(self._list)

        else:
            return Response(406, 'Not Acceptable')

        body = body.encode('utf-8')
        headers = [('Content-Type', content_type),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)

    def get_html(self):
        html = f'<html><head></head><body><div>Notes ({len(self._list)})' \
               f'</div><ul>'
        for k, v in self._list.items():
            html += f'<li>#{k} {v}</li>'
        html += '</ul></body></html>'
        return html

    def del_text(self, n):
        self._list.pop(int(n))

    def send_response(self, connection, res):
        with connection.makefile('wb') as file:
            file.write(self.status_to_str(res).encode('utf-8'))
            file.write(self.headers_to_str(res).encode('utf-8'))
            file.write(b'\r\n')
            if res.body:
                file.write(res.body)
            file.flush()

    @staticmethod
    def headers_to_str(res):
        line = ''
        if res.headers:
            for (key, value) in res.headers:
                line += f'{key}: {value}\r\n'
        return line

    @staticmethod
    def status_to_str(res):
        return f'HTTP/1.1 {res.status} {res.reason}\r\n'


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
        res = f'method: {self.method}\n'
        res += f'target: {self.target}\n'
        res += f'version: {self.version}\n'
        res += f'headers: {self.headers}\n'
        res += f'file: {self.file}\n'
        res += f'user: {self.user}\n'
        res += f'url: {self.url}\n'
        res += f'path: {self.path}\n'
        res += f'query: {self.query}\n'
        return res


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    def __str__(self):
        res = f'status: {self.status}\n'
        res += f'reason: {self.reason}\n'
        res += f'headers: {self.headers}\n'
        res += f'body: {self.body}\n'
        return res


class Error(Exception):
    def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body


if __name__ == '__main__':
    with open(CONFIG_PATH) as cfg:
        data = json.load(cfg)
    server = Server(data['host'], data['port'], data['server'])
    with server as s:
        s.serve()
