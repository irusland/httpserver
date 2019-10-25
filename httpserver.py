# python3

import json
import socket
import sys
from email.parser import Parser
from urllib.parse import parse_qs, urlparse


class Server:
    MAX_LINE = 64 * 1024
    MAX_HEADERS = 100

    def __init__(self, host, port, server_name):
        self._host = host
        self._port = port
        self._server_name = server_name
        self._list = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self

    def serve(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self._host, self._port))
        sock.listen()

        while True:
            connection, _ = sock.accept()
            self.serve_client(connection)

    def serve_client(self, connection):
        try:
            req = self.parse_request(connection)
            print(f'Got request {req}')
            res = self.handle_request(req)
            print(f'Response {res}')
            self.send_response(connection, res)
        except ConnectionResetError:
            connection = None
        except Exception as e:
            connection.close()
            self.send_error(connection, e)

        if connection:
            req.file.close()
            connection.close()

    def send_error(self, conn, err):
        try:
            status = err.status
            reason = err.reason
            body = (err.body or err.reason).encode('utf-8')
        except:
            status = 500
            reason = b'Internal Server Error'
            body = b'Internal Server Error'
        resp = Response(status, reason, [('Content-Length', len(body))], body)
        self.send_response(conn, resp)

    def parse_request(self, connection):
        file = connection.makefile('rb')
        method, target, ver = self.parse_request_line(file)
        headers = self.parse_headers(file)
        host = headers.get('Host')
        if not host:
            raise Error(400, 'Bad request',
                        'Host header is missing')
        if host not in (self._server_name,
                        f'{self._server_name}:{self._port}'):
            raise Error(404, 'Not found')
        return Request(method, target, ver, headers, file, connection.getpeername())

    def parse_request_line(self, reqfile):
        raw = reqfile.readline(self.MAX_LINE + 1)
        if len(raw) > self.MAX_LINE:
            raise Error(400, 'Bad request',
                        'Request line is too long')

        req_line = str(raw, 'utf-8')
        words = req_line.split()
        if len(words) != 3:
            raise Error(400, 'Bad request',
                        'Malformed request line')

        method, target, ver = words
        if ver != 'HTTP/1.1':
            raise Error(505, 'HTTP Version Not Supported')
        return method, target, ver

    def parse_headers(self, rfile):
        headers = []
        while True:
            line = rfile.readline(self.MAX_LINE + 1)
            if len(line) > self.MAX_LINE:
                raise Error(494, 'Request header too large')

            if line in (b'\r\n', b'\n', b''):
                break

            headers.append(line)
            if len(headers) > self.MAX_HEADERS:
                raise Error(494, 'Too many headers')

        sheaders = b''.join(headers).decode('utf-8')
        return Parser().parsestr(sheaders)

    def handle_request(self, req):
        if req.path == '/add':
            return self.add_text(req)

        if req.path == '/cls':
            return self.clear_text()

        if req.path == '/' and req.method == 'GET':
            return self.show_text(req)

        if req.path.startswith('/del/'):
            number = req.path[len('/del/'):]
            if number.isdigit():
                return self.del_text(req, number)

        raise Error(404, 'Not found')

    def clear_text(self):
        self._list.clear()
        return Response(204, f'Cleared')

    def add_text(self, req):
        id = len(self._list) + 1
        self._list[id] = req.query['text'][0]
        textres = f'<html><head></head><body> Text added {req.query["text"][0]}</body></html>'
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
        html = '<html><head></head><body>'
        html += f'<div>Заметки ({len(self._list)})</div>'
        html += '<ul>'
        for k, v in self._list.items():
            html += f'<li>#{k} {v}</li>'
        html += '</ul>'
        html += '</body></html>'
        return html

    def del_text(self, req, id):
        self._list.pop(int(id))

    def send_response(self, connection, res):
        wfile = connection.makefile('wb')
        wfile.write(self.status_to_str(res).encode('utf-8'))
        wfile.write(self.headers_to_str(res).encode('utf-8'))
        wfile.write(b'\r\n')
        if res.body:
            wfile.write(res.body)
        wfile.flush()
        wfile.close()

    def headers_to_str(self, res):
        line = ''
        if res.headers:
            for (key, value) in res.headers:
                line += f'{key}: {value}\r\n'
        return line

    def status_to_str(self, res):
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
        res = f'method {self.method}\n'
        res += f'target {self.target}\n'
        res += f'version {self.version}\n'
        res += f'headers {self.headers}\n'
        res += f'file {self.file}\n'
        res += f'user {self.user}\n'
        res += f'url {self.url}\n'
        res += f'path {self.path}\n'
        res += f'query {self.query}\n'
        return res


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    def __str__(self):
        res = f'status {self.status}\n'
        res += f'reason {self.reason}\n'
        res += f'headers {self.headers}\n'
        res += f'body {self.body}\n'
        return res


class Error(Exception):
    def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body


if __name__ == '__main__':
    with open('config.json') as cfg:
        data = json.load(cfg)
    server = Server(data['host'], data['port'], data["server"])
    with server as s:
        s.serve()
