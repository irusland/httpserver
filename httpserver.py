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
from pathfinder import PathFinder

import magic
import logging
import chardet


class Server:
    MAX_LINE = 64 * 1024
    MAX_SEND_SIZE = 1024
    MAX_HEADERS = 100
    BREAKLINE = [b'\r\n', b'\n', b'']

    def __init__(self, host, port, debug=True, refresh_rate=0):
        self._host = host
        self._port = port
        self._list = {}
        self._debug = debug
        self.ruler = PathFinder()
        self._running = True
        self.refresh_rate = refresh_rate

        self.addr = (host, port)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.poller = selectors.DefaultSelector()
        socket.setdefaulttimeout(refresh_rate)
        self.conns = {}

        logging.basicConfig(filename=LOGGER_PATH, level=logging.INFO,
                            filemode='w')

    def __enter__(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.addr)
        self.server.listen()
        self.server.setblocking(False)
        logging.info(f'server is UP on {self._host}:{self._port}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type != KeyboardInterrupt:
            logging.exception(f'server is DOWN because of exception '
                              f'{exc_type} {exc_val} {exc_tb}')
        else:
            logging.info('server is DOWN with no exceptions')
        self._running = False
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
        # client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.poller.register(client, selectors.EVENT_READ, self._read)

    def _read(self, client, mask):
        try:
            t = threading.Thread(target=self.serve_client,
                                 args=(client,))
            t.start()
            logging.info(f'Threaded client serving '
                         f'started {client.getpeername()} in '
                         f'thread {threading.current_thread().ident}')
        except Exception as e:
            logging.info(f'Socket in thread {threading.current_thread().ident}'
                         f' was disconnected')
            self._close(client)

    def _close(self, connection):
        logging.info(f'Socket Disconnected in thread '
                     f'{threading.current_thread().ident}')
        self.poller.unregister(connection)
        del self.conns[connection.fileno()]
        connection.close()

    def serve_client(self, connection):
        try:
            req = self.parse_req_connection(connection)
            logging.info(f'Request parsed from {req.user} {req}')
            res = self.handle_req(req)
            logging.info(f'Response prepared \n{res}')
            self.send_response(connection, res)
            logging.info(f'Response sent \n{res}')
        except Exception as e:
            logging.exception(f'Client handling failed '
                              f'({threading.current_thread().ident}) {e}')
            self.send_error(connection, e)

    def send_error(self, connection, err):
        try:
            if err.page:
                with open(err.page, 'rb') as p:
                    p = p.read()

                res = [self.build_err_res(err.status, err.reason, p)]
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

    def parse_req_connection(self, client):
        req_bytes = self.receive_from_client(client)
        file = io.BytesIO(req_bytes)
        logging.info(f'Request parsing by connection started')
        req = self.parse_req_file(file)
        request = self.parsed_req_to_request(
            *req, file, client.getpeername())

        logging.info(f'Request parsed')
        return request

    def receive_from_client(self, client):
        data = []
        while True:
            try:
                line = client.recv(self.MAX_LINE)
                if line in self.BREAKLINE:
                    break
                data.append(line)
            except socket.error as e:
                break
        data = b''.join(data)
        if not data:
            logging.error('No data received')
            raise Exception('No data received')
        return data

    def parsed_req_to_request(self, method, target,
                              ver, headers, file, peername=None):
        return Request(method, target, ver, headers, file, peername)

    def parse_req_file(self, file):
        logging.info(f'Parsing request by file started')
        method, target, ver = self.parse_request_line(file)
        headers = self.parse_headers_from_file(file)
        host = headers.get('Host')
        if not host:
            raise Errors.HEADER_MISSING
        return method, target, ver, headers

    def parse_request_line(self, file):
        raw = file.readline(self.MAX_LINE + 1)
        if len(raw) > self.MAX_LINE:
            raise Errors.REQ_TOO_LONG
        req_line = (self.decode(raw))

        try:
            method, target, ver = req_line.split()
        except ValueError as e:
            logging.error(f'Could not parse request {req_line} {e}')
            raise Errors.MALFORMED_REQ

        if ver != 'HTTP/1.1':
            raise Errors.VERSION_NOT_SUPPORTED
        return method, target, ver

    def parse_headers_from_file(self, rfile):
        headers = []

        while True:
            line = rfile.readline(self.MAX_LINE + 1)
            if len(line) > self.MAX_LINE:
                raise Errors.HEADER_TOO_LARGE
            if line in self.BREAKLINE:
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
                return self.build_res(req, destination, content_type)
            raise Errors.NOT_FOUND

    def build_res(self, req, path, content_type):
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

    def send_response(self, client, *res):
        try:
            ip = client.getpeername()
        except socket.error as e:
            if str(e) == '[Errno 9] Bad file descriptor':
                logging.error(f'Connection with client broken')
            return

        for response in res:
            contents = b''.join((
                self.status_to_str(response).encode('utf-8'),
                self.headers_to_str(response).encode('utf-8'),
                b'\r\n',
                response.body
            ))
            try:
                while contents:
                    try:
                        bytes_sent = client.send(contents)
                        contents = contents[bytes_sent:]
                        logging.info(f'{bytes_sent}B sent to {ip}')
                    except socket.error as e:
                        if str(e) == "[Errno 35] Resource " \
                                     "temporarily unavailable":
                            logging.error('[Errno 35] Resource temporarily '
                                          'unavailable Sleeping 0.1s')
                            time.sleep(0.1)
                        elif str(e) == "[Errno 32] Broken pipe":
                            msg = f'client stopped receiving {e}'
                            logging.exception(msg)
                            raise e
                        elif str(e) == '[Errno 9] Bad file descriptor':
                            logging.error(f'Connection with client {ip} broken')
                            raise e
            except socket.error as e:
                logging.error(e)
                raise e
            else:
                logging.info(f'Files sent to {ip}')

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
    server = Server(data['host'], data['port'])
    with server as s:
        s.serve()
