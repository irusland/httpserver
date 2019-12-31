# python3
import argparse
import io
import re
import select
import selectors
import socket
import threading
import time
from functools import reduce
from queue import Queue

from diskcache import Cache

from backend import errors
from backend.configurator import Configurator
from defenitions import CONFIG_PATH, LOGGER_PATH
from backend.router.router import Router

from backend.request import Request
from backend.response import Response
from backend.errors import Errors, KeepAliveExpire

from backend.logger import Logger, LogLevel


class Server:
    MAX_LINE = 64 * 1024
    MAX_SEND_SIZE = 1024
    MAX_HEADERS = 100
    BREAKLINE = [b'', b'\n']

    def __init__(self, config=CONFIG_PATH,
                 loglevel=LogLevel.LOGGING,
                 refresh_rate=0.1,
                 cache_max_size=4e9,
                 log_path=None):

        Logger.configure(level=loglevel, info_path=log_path)

        self.configurator = Configurator.init(config)

        self.router = Router()
        self.router.load_handlers(self.configurator.get_rules())

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
        self.requests = {}
        self.out_buff = {}

    def __enter__(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.address)
        self.server.listen()
        self.server.setblocking(False)
        Logger.debug_info(f'server is UP on {self._host}:{self._port}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and exc_type is not KeyboardInterrupt:
            Logger.exception(f'server is DOWN because of exception ')
        else:
            Logger.debug_info('server is DOWN with no exceptions')
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
            for key, m in poll:
                try:
                    callback = key.data
                    callback(key.fileobj)
                except socket.error as e:
                    if e.errno == 54:
                        Logger.debug_info(f'Disconnected {key.fileobj}')

    def _accept(self, sock):
        (client, addr) = sock.accept()
        num = client.fileno()
        self.conns[num] = client
        self.requests[num] = Request()
        self.out_buff[num] = []
        Logger.debug_info(f'Connected {addr}')

        client.setblocking(False)
        self.poller.register(client,
                             selectors.EVENT_READ,
                             self._read)
        Logger.debug_info(f'EVENT_READ Registered {addr}')

    @staticmethod
    def split_keep_sep(s: bytes, sep):
        xs = re.split(rb'(%s)' % re.escape(sep), s)
        return [xs[i] + (xs[i + 1] if i + 1 < len(xs) else b'')
                for i in range(0, len(xs), 2)]

    def _read(self, client):
        try:
            line: bytes = client.recv(self.MAX_LINE)
            if not line:
                return
            num = client.fileno()
            req_builder: Request = self.requests[num]
            split = self.split_keep_sep(line, b'\r\n')

            for s in split:
                if req_builder.dynamic_fill(s):
                    self.requests[num] = Request()
                    return self.serve_client(client, req_builder)
        except Exception as e:
            errors.send_error(client, e)

    def parse_req_file(self, file):
        Logger.debug_info(f'Parsing request by file started')
        method, target, ver = self.parse_request_line(file)
        headers = self.parse_headers_from_file(file)
        body = self.parse_body(file)
        host = headers.get('Host')
        if not host:
            raise Errors.HEADER_MISSING
        return method, target, ver, headers, body

    def _write(self, client):
        num = client.fileno()
        buffer_: list = self.out_buff[num]
        if not buffer_:
            return
        bytes_sent = client.sendall(buffer_[0])
        del buffer_[0]
        Logger.debug_info(
            f'{bytes_sent}B sent to {num} {buffer_} left')

    def close(self, connection):
        try:
            self.poller.unregister(connection)
            del self.conns[connection.fileno()]
        except Exception:
            Logger.debug_info('Socket disconnected by timeout')
        connection.close()
        Logger.debug_info(f'Socket Disconnected in thread '
                          f'{threading.current_thread().ident}')

    def serve_client(self, client, req: Request):
        try:
            if self.insufficient(req):
                raise Errors.MALFORMED_REQ
            Logger.debug_info(f'Request got {req}',
                              extra={'url': req.path})
            a = time.perf_counter()
            res = self.handle_req(req)
            Logger.debug_info(
                f'Request handling time {time.perf_counter() - a}',
                extra={'url': req.path})
            Logger.debug_info(f'Response prepared {res}',
                              extra={'url': req.path, 'code': res.status})

            Response.send_response(client, res)
            Logger.debug_info(f'Response sent',
                              extra={'url': req.path, 'code': res.status})

            Logger.info(f'Source Requested',
                        extra={'method': req.method,
                               'url': req.path,
                               'code': res.status,
                               'ip': client.getpeername()})

            if req.headers.get('Connection') == 'keep-alive':
                client.setsockopt(socket.SOL_SOCKET,
                                  socket.SO_KEEPALIVE, 1)
            if req.headers.get('Connection') == 'close':
                self.close(client)
        except KeepAliveExpire:
            Logger.debug_info(f'Keep-alive connection is not alive, '
                              f'disconnecting')
            self.close(client)
        except Exception as e:
            Logger.error(f'Client handling failed', e)
            errors.send_error(client, e)
            Logger.error(f'Error sent')

    def parse_body(self, file):
        return file.read()

    def parse_request_line(self, file):
        raw = file.readline(self.MAX_LINE + 1)
        if len(raw) > self.MAX_LINE:
            raise Errors.REQ_TOO_LONG
        req_line = (Request.decode(raw))

        try:
            method, target, ver = req_line.split()
        except ValueError as e:
            Logger.error(f'Could not parse request')
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
        rules = self.configurator.get_rules()
        handle = self.router.find_handler(req, rules)
        if handle:
            return handle(req, self)
        else:
            Logger.error('Handler not found', extra={'url': req.path})
            raise Errors.NO_HANDLER

    @staticmethod
    def insufficient(req: Request):
        if not req.method or not req.path or not req.version:
            return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        help='Specify server config path',
                        default=CONFIG_PATH)
    parser.add_argument('-l', '--loglevel',
                        help='Use module to write logs',
                        type=LogLevel.from_string,
                        default=LogLevel.from_string('console'),
                        choices=list(LogLevel))
    parser.add_argument('--log-path',
                        help='Specify logger file path',
                        default=LOGGER_PATH)

    args = parser.parse_args()

    server = Server(config=args.config, loglevel=args.loglevel,
                    log_path=args.log_path)
    with server as s:
        s.serve()
