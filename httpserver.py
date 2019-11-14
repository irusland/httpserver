# python3
import io
import json
import os
import selectors
import socket
import threading
import time

from email.parser import Parser
from urllib.parse import parse_qs, urlparse

from defenitions import CONFIG_PATH, LOGGER_PATH
from ruler import Ruler

import magic
import logging
import chardet


class Server:
    MAX_LINE = 64 * 1024
    MAX_SEND_SIZE = 1024
    MAX_HEADERS = 100

    def __init__(self, host, port, server_name, debug=True, refresh_rate=0):
        self._host = host
        self._port = port
        self._server_name = server_name
        self._list = {}
        self._debug = debug
        self.ruler = Ruler()
        self._running = True
        self.refresh_rate = refresh_rate

        self.addr = (host, port)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.poller = selectors.DefaultSelector()
        socket.setdefaulttimeout(refresh_rate)
        self.conns = {}

        logging.basicConfig(filename=LOGGER_PATH, level=logging.INFO)

    def __enter__(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.addr)
        self.server.listen()
        self.server.setblocking(False)
        logging.info(f'server is UP on {self._host}:{self._port}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO Exception handling from serve_client
        # TODO Ask about zombie lasting threads
        logging.exception(exc_val)
        self._running = False
        logging.info('server is DOWN')
        self.poller.close()
        self.server.close()
        return False

    def shutdown(self):
        self.server.close()
        self._running = False

    def serve(self):
        self.conns[self.server.fileno()] = self.server
        self.poller.register(self.server, selectors.EVENT_READ,
                             self._accept)

        while self._running:
            poll = self.poller.select(self.refresh_rate)
            for key, mask in poll:
                callback = key.data
                callback(key.fileobj, mask)

    def _accept(self, sock, mask):
        (client, addr) = sock.accept()
        self.conns[client.fileno()] = client
        logging.info(f'Connected {addr}')

        client.setblocking(False)
        self.poller.register(client, selectors.EVENT_READ, self._read)

    def _read(self, sock, mask):
        t = threading.Thread(target=self.serve_client,
                             args=(sock,))
        t.start()
        logging.info(f'Threaded client serving started {sock.getpeername()}')

    def serve_client(self, connection):
        try:
            req = self.parse_req_connection(connection)
            logging.info(f'Got request from {req.user} {req}')
            res = self.handle_req(req)
            logging.info(f'Response {res}')
            self.send_response(connection, res)
        except Exception as e:
            logging.exception(e)
            self.send_error(connection, e)

        logging.info(f'Disconnected {connection.getpeername()}')
        self.poller.unregister(connection)
        del self.conns[connection.fileno()]
        connection.close()

    def send_error(self, connection, err):
        try:
            if err.page:
                with open(err.page, 'rb') as p:
                    p = p.read()
                styles = []
                for style in err.page_styles:
                    with open(style, 'rb') as s:
                        styles.append(s.read())

                res = self.build_err_res(err.status, err.reason, p)
                res_css = [self.build_err_res(err.status,
                                              err.reason,
                                              s,
                                              css=True) for s in styles]
                res = [res, *res_css]
            else:
                res = [self.build_err_res(
                    err.status, err.reason,
                    (err.body or err.reason).encode('utf-8'))]
        except AttributeError as e:
            res = [self.build_err_res(500, b'Internal Server Error',
                                      b'Internal Server Error')]
        self.send_response(connection, *res)

    @staticmethod
    def build_err_res(status, reason, body, css=False):
        return Response(
            status, reason,
            [('Content-Type', f'text/{"css" if css else "html"}'),
             ('Content-Length', len(body))], body)

    def parse_req_connection(self, connection):
        with connection.makefile('rb') as file:
            return self.parsed_req_to_request(
                *self.parse_req_file(file), file, connection.getpeername())

    def parsed_req_to_request(self, method, target,
                              ver, headers, file, peername=None):
        return Request(method, target, ver, headers, file, peername)

    def parse_req_file(self, file):
        method, target, ver = self.parse_request_line(file)
        headers = self.parse_headers_from_file(file)
        host = headers.get('Host')
        if not host:
            raise Errors.HEADER_MISSING
        if host not in (self._server_name,
                        f'{self._server_name}:{self._port}'):
            raise Errors.NOT_FOUND
        return method, target, ver, headers

    def parse_request_line(self, file):
        raw = file.readline(self.MAX_LINE + 1)
        if len(raw) > self.MAX_LINE:
            raise Errors.REQ_TOO_LONG
        req_line = (self.decode(raw))

        try:
            method, target, ver = req_line.split()
        except ValueError as e:
            raise Errors.MALFORMED_REQ

        if ver != 'HTTP/1.1':
            raise Errors.VERSION_NOT_SUPPORTED
        return method, target, ver

    def parse_headers_from_file(self, rfile):
        headers = []
        breakline = [b'\r\n', b'\n', b'']

        while True:
            line = rfile.readline(self.MAX_LINE + 1)
            if len(line) > self.MAX_LINE:
                raise Errors.HEADER_TOO_LARGE
            if line in breakline:
                break
            headers.append(line)
            if len(headers) > self.MAX_HEADERS:
                raise Errors.TOO_MANY_HEADERS

        headers = b''.join(headers)
        return self.parse_headers_str(self.decode(headers))

    def decode(self, b):
        encoding = chardet.detect(b)['encoding']
        if encoding:
            return str(b, encoding)
        return str(b)

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
                raise Errors.NOT_FOUND
            if destination:
                content_type = self.ruler.get_type(req.path, rules)
                if not content_type:
                    mime = magic.Magic(mime=True)
                    content_type = mime.from_file(destination)
                logging.info(f'{destination} type {content_type}')
                return self.send_file(req, destination, content_type)
        raise Errors.NOT_FOUND

    def send_file(self, req, path, content_type):
        accept = req.headers.get('Accept')
        if content_type in accept or '*/*' in accept:
            with open(path, 'rb') as file:
                body = file.read()
        else:
            return Response(406, 'Not Acceptable')
        filename = os.path.basename(path)
        headers = [('Content-Type', f'{content_type}'),
                   ('Content-Disposition', f'inline; filename={filename}'),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)

    def send_response(self, connection, *res):
        for response in res:
            contents = b''.join((
                self.status_to_str(response).encode('utf-8'),
                self.headers_to_str(response).encode('utf-8'),
                b'\r\n',
                response.body
            ))
            peer = connection.getpeername()
            while contents:
                try:
                    bytes_sent = connection.send(contents)
                    contents = contents[bytes_sent:]
                    logging.info(f'{bytes_sent}B sent to {peer}')
                except socket.error as e:
                    # TODO ask about fixing this
                    if str(e) == "[Errno 35] Resource temporarily unavailable":
                        logging.error('[Errno 35] Resource temporarily '
                                      'unavailable Sleeping 0.1s')
                        time.sleep(0.1)
                    elif str(e) == "[Errno 32] Broken pipe":
                        msg = f'client stopped receiving {e}'
                        logging.exception(msg)
                        raise e
                    else:
                        raise e
            logging.info(f'File sent to {connection.getpeername()}')

    @staticmethod
    def headers_to_str(res):
        return ''.join(f'{k}: {v}\r\n' for (k, v) in res.headers)

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
        return '\n'.join(f'{k}: {v}' for k, v in self.__dict__.items())


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    def __str__(self):
        lim = 500
        return '\n'.join(
            f'{k}: {str(v) if len(str(v)) < lim else str(v)[:lim]}'
            for k, v in self.__dict__.items())


class Error(Exception):
    def __init__(self, status, reason, body=None, page=None):
        self.status = status
        self.reason = reason
        self.body = body
        if page:
            with open(CONFIG_PATH) as cfg:
                data = json.load(cfg)
                self.page = data["error-pages"][page]
                self.page_styles = data["error-pages"]['styles']


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


if __name__ == '__main__':
    with open(CONFIG_PATH) as cfg:
        data = json.load(cfg)
    server = Server(data['host'], data['port'], data['server'])
    with server as s:
        s.serve()
