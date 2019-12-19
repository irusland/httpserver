# python3
import argparse
import io
import select
import selectors
import socket
import threading
import time
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

        Logger.configure(level=loglevel, path=log_path)

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
        Logger.info(f'server is UP on {self._host}:{self._port}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and exc_type is not KeyboardInterrupt:
            Logger.exception(f'server is DOWN because of exception ')
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
            for key, m in poll:
                callback = key.data
                # print(key.data, 'event', key.events, 'mask', m,
                #       'write is', selectors.EVENT_WRITE,
                #       'read is', selectors.EVENT_READ)
                callback(key.fileobj)

    def _accept(self, sock):
        (client, addr) = sock.accept()
        self.conns[client.fileno()] = client
        self.requests[client.fileno()] = Request()
        self.out_buff[client.fileno()] = []
        Logger.info(f'Connected {addr}')

        client.setblocking(False)
        self.poller.register(client,
                             selectors.EVENT_READ,
                             self._read)
        Logger.info(f'EVENT_READ Registered {addr}')

    def _read(self, client):
        line: bytes = client.recv(self.MAX_LINE)
        req_builder: Request = self.requests[client.fileno()]

        split = line.splitlines()
        for s in split:
            if req_builder.dynamic_fill(s):
                self.requests[client.fileno()] = Request()
                return self.serve_client(client, req_builder)

    def parse_req(self, req_bytes):
        file = io.BytesIO(req_bytes)
        Logger.info(f'Request parsing by connection started')
        req = self.parse_req_file(file)
        request = Request.parsed_req_to_request(
            *req, file)

        Logger.info(f'Request parsed')
        return request

    def parse_req_file(self, file):
        Logger.info(f'Parsing request by file started')
        method, target, ver = self.parse_request_line(file)
        headers = self.parse_headers_from_file(file)
        body = self.parse_body(file)
        host = headers.get('Host')
        if not host:
            raise Errors.HEADER_MISSING
        return method, target, ver, headers, body

    def _write(self, client):
        buffer_: list = self.out_buff[client.fileno()]
        if len(buffer_) == 0:
            return
        bytes_sent = client.sendall(buffer_[0])
        del buffer_[0]
        Logger.info(f'{bytes_sent}B sent to {client.fileno()} {buffer_} left')

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

    def serve_client(self, client, req):
        try:
            # print(req)
            Logger.info(f'Request parsed from {req.user}',
                        extra={'url': req.path})
            a = time.perf_counter()
            res = self.handle_req(req)
            Logger.info(f'Request handling time {time.perf_counter() - a}',
                        extra={'url': req.path})
            Logger.info(f'Response prepared ',
                        extra={'url': req.path, 'code': res.status})

            Response.send_response(client, res)
            Logger.info(f'Response sent',
                        extra={'url': req.path, 'code': res.status})

            if req.headers.get('Connection') == 'keep-alive':
                client.setsockopt(socket.SOL_SOCKET,
                                  socket.SO_KEEPALIVE, 1)
            else:
                self._close(client)
        except KeepAliveExpire:
            Logger.info(f'Keep-alive connection is not alive, '
                        f'disconnecting')
            self._close(client)
        except Exception as e:
            Logger.error(f'Client handling failed '
                         f'({threading.current_thread().ident})')
            errors.send_error(client, e)
            Logger.error(f'Error sent to '
                         f'({threading.current_thread().ident})')

    def receive_from_client(self, client, client_timeout=0):
        buffer_ = []
        client.settimeout(client_timeout)
        while True:
            try:
                line = client.recv(self.MAX_LINE)
                if line in self.BREAKLINE:
                    print(f'"{line}"')
                    break
                buffer_.append(line)
                # if line.endswith(b'\r\n\r\n'):
                #     break
                print(f'GOT LINE {line}', buffer_)
            except socket.error as e:
                if e.errno == 35:
                    # time.sleep(0.5)
                    break
                break
        buffer_ = b''.join(buffer_)
        if not buffer_:
            Logger.error('No data received')
            raise KeepAliveExpire()
        return buffer_

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
