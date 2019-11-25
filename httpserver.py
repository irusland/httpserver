# python3
import io
import json
import selectors
import socket
import threading
import urllib.parse

from defenitions import CONFIG_PATH, LOGGER_PATH
from errors import Errors
from pathfinder import PathFinder

import magic
import logging

from request import Request
from response import Response


class Server:
    MAX_LINE = 64 * 1024
    MAX_SEND_SIZE = 1024
    MAX_HEADERS = 100
    BREAKLINE = [b'\r\n', b'\n', b'']

    def __init__(self, host, port, debug=True, refresh_rate=0):
        self._host = host
        self._port = port
        self._debug = debug
        self.finder = PathFinder()
        self._running = True
        self.refresh_rate = refresh_rate

        self.addr = (host, port)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.poller = selectors.DefaultSelector()
        socket.setdefaulttimeout(refresh_rate)
        self.conns = {}

        logging.basicConfig(filename=LOGGER_PATH, level=logging.INFO,
                            filemode='w+')

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
            for key, _ in poll:
                callback = key.data
                callback(key.fileobj)

    def _accept(self, sock):
        (client, addr) = sock.accept()
        self.conns[client.fileno()] = client
        logging.info(f'Connected {addr}')

        client.setblocking(False)
        # client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.poller.register(client, selectors.EVENT_READ, self._handle)

    def _handle(self, client):
        try:
            t = threading.Thread(target=self.serve_client,
                                 args=(client,))
            t.start()
            logging.info(f'Threaded client serving '
                         f'started {client.getpeername()} in '
                         f'thread {threading.current_thread().ident}')
        except socket.error as e:
            logging.info(f'Socket in thread {threading.current_thread().ident}'
                         f' was disconnected {e}')
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
            Response.send_response(connection, res)
            logging.info(f'Response sent \n{res}')
        except Exception as e:
            logging.exception(f'Client handling failed '
                              f'({threading.current_thread().ident}) {e}')
            Errors.send_error(connection, e)

    def parse_req_connection(self, client):
        req_bytes = self.receive_from_client(client)
        file = io.BytesIO(req_bytes)
        logging.info(f'Request parsing by connection started')
        req = self.parse_req_file(file)
        request = Request.parsed_req_to_request(
            *req, file, client.getpeername())

        logging.info(f'Request parsed')
        return request

    def receive_from_client(self, client):
        buffer = []
        while True:
            try:
                line = client.recv(self.MAX_LINE)
                if line in self.BREAKLINE:
                    break
                buffer.append(line)
            except socket.error:
                break
        buffer = b''.join(buffer)
        if not buffer:
            logging.error('No data received')
            raise Exception('No data received')
        return buffer

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
        req_line = (Request.decode(raw))

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
        return Request.parse_headers_str(Request.decode(headers))

    def handle_req(self, req):
        if req.path.startswith('/') and req.method == 'GET':
            rules = self.finder.get_rules()
            try:
                # Or use unquote_plus (translates + as space)
                path = urllib.parse.unquote(req.path)
                destination = self.finder.get_destination(path, rules, True)
            except FileNotFoundError:
                raise Errors.NOT_FOUND
            if destination:
                content_type = self.finder.get_type(req.path, rules)
                if not content_type:
                    mime = magic.Magic(mime=True)
                    content_type = mime.from_file(destination)
                return Response.build_res(req, destination, content_type)
            raise Errors.NOT_FOUND


if __name__ == '__main__':
    with open(CONFIG_PATH) as cfg:
        data = json.load(cfg)
    server = Server(data['host'], data['port'])
    with server as s:
        s.serve()
