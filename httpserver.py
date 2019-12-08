# python3
import argparse
import io
import selectors
import socket
import threading
import time
import urllib.parse

from diskcache import Cache

from backend.argparser import ArgParser
from backend.configurator import Configurator
from defenitions import CONFIG_PATH, REQUEST_HANDLERS_DIR
from backend.router.router import Router

import magic

from backend.request import Request
from backend.response import Response
from backend.errors import Errors

from backend.logger import Logger, LogLevel


class Server:
    MAX_LINE = 64 * 1024
    MAX_SEND_SIZE = 1024
    MAX_HEADERS = 100
    BREAKLINE = [b'\r\n', b'\n', b'']

    def __init__(self, config=CONFIG_PATH,
                 loglevel=LogLevel.logging,
                 refresh_rate=0.1,
                 cache_max_size=4e9,
                 log_path=None):

        Logger.configure(level=loglevel, path=log_path)
        self.configurator = Configurator.init(config)

        self.router = Router()

        self.cache = Cache(size_limit=int(cache_max_size))

        self._host = self.configurator.get('host')
        self._port = self.configurator.get('port')
        self.address = (self._host, self._port)
        self._running = True
        self.refresh_rate = refresh_rate

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.poller = selectors.DefaultSelector()
        socket.setdefaulttimeout(refresh_rate)
        self.conns = {}

    def __enter__(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.address)
        self.server.listen()
        self.server.setblocking(False)
        Logger.info(f'server is UP on {self._host}:{self._port}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            Logger.exception(f'server is DOWN because of exception '
                             f'{exc_type} {exc_val} {exc_tb}')
        else:
            Logger.info('server is DOWN with no exceptions')
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
        Logger.info(f'Connected {addr}')

        client.setblocking(False)
        self.poller.register(client, selectors.EVENT_READ, self._handle)

    def _handle(self, client):
        try:
            t = threading.Thread(target=self.serve_client,
                                 args=(client,))
            t.start()
            Logger.info(f'Threaded client serving '
                        f'started {client.getpeername()} in '
                        f'thread {threading.current_thread().ident}')
        except socket.error as e:
            Logger.info(f'Socket in thread {threading.current_thread().ident} '
                        f'was disconnected {e}')
            self._close(client)

    def _close(self, connection):
        try:
            self.poller.unregister(connection)
            del self.conns[connection.fileno()]
        except Exception:
            Logger.info('Socket disconnected by timeout')
        connection.close()
        Logger.info(f'Socket Disconnected in thread '
                    f'{threading.current_thread().ident}')

    def serve_client(self, connection):
        try:
            req = self.parse_req_connection(connection)
            Logger.info(f'Request parsed from {req.user} {req}',
                        extra={'url': req.path})
            a = time.perf_counter()
            res = self.handle_req(req)
            Logger.info(f'Request handling time {time.perf_counter() - a}',
                        extra={'url': req.path})
            Logger.info(f'Response prepared \n{res}',
                        extra={'url': req.path, 'code': res.status})
            Response.send_response(connection, res)
            Logger.info(f'Response sent \n{res}',
                        extra={'url': req.path, 'code': res.status})

            if req.headers.get('Connection') == 'keep-alive':
                connection.setsockopt(socket.SOL_SOCKET,
                                      socket.SO_KEEPALIVE, 1)
            else:
                self._close(connection)
        except Exception as e:
            if str(e) == 'No data received':
                Logger.info(f'Keep-alive connection is not alive, '
                            f'disconnecting')
                self._close(connection)
                return
            Logger.exception(f'Client handling failed '
                             f'({threading.current_thread().ident}) {e}')
            Errors.send_error(connection, e)

    def parse_req_connection(self, client):
        req_bytes = self.receive_from_client(client)
        file = io.BytesIO(req_bytes)
        Logger.info(f'Request parsing by connection started')
        req = self.parse_req_file(file)
        request = Request.parsed_req_to_request(
            *req, file, client.getpeername())

        Logger.info(f'Request parsed')
        return request

    def receive_from_client(self, client):
        buffer_ = []
        while True:
            try:
                line = client.recv(self.MAX_LINE)
                if line in self.BREAKLINE:
                    break
                buffer_.append(line)
            except socket.error:
                break
        buffer_ = b''.join(buffer_)
        if not buffer_:
            Logger.error('No data received')
            raise Exception('No data received')
        return buffer_

    def parse_req_file(self, file):
        Logger.info(f'Parsing request by file started')
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
            Logger.error(f'Could not parse request {req_line} {e}')
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
        # todo add handlers
        handle = self.router.find_handler(req)
        if handle:
            Logger.info('Handler found', extra={'url': req.path})
            return handle(req, self)
        else:
            Logger.error('Handler not found', extra={'url': req.path})
            raise Errors.NOT_FOUND


if __name__ == '__main__':
    parser = ArgParser()
    args = parser.parse_args()

    server = Server(config=args.config, loglevel=args.loglevel,
                    log_path=args.log_path)
    with server as s:
        s.serve()
