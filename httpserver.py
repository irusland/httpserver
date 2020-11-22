import argparse
import os
import selectors
import socket
import threading
import time

from diskcache import Cache

from backend import errors
from backend.configurator import Configurator
from defenitions import CONFIG_PATH, LOGGER_PATH, LOG_DEBUG_PATH
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
                 server_log=None,
                 debug_log=None):

        Logger.configure(level=loglevel, info_path=server_log,
                         debug_path=debug_log)

        self.configurator = Configurator(config)

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
        self.poller.register(self.server, selectors.EVENT_READ, self._accept)

        while self._running:
            poll = self.poller.select(self.refresh_rate)
            for key, mask in poll:
                try:
                    callback = key.data
                    callback(key.fileobj, mask)
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
                             self._on_read_write_event)
        Logger.debug_info(f'EVENT_READ Registered {addr}')

    def _on_read_write_event(self, client):
        try:
            line: bytes = client.recv(self.MAX_LINE)
            if not line:
                self.poller.unregister(client)
                del self.conns[client.fileno()]
                return
            num = client.fileno()
            req_builder: Request = self.requests[num]
            split = Request.split_keep_sep(line, bytes(os.linesep, 'utf-8'))

            for s in split:
                if req_builder.dynamic_fill(s):
                    self.requests[num] = Request()  # todo possibly
                                        # todo Request() change to req_builder
                    return self.serve_client(client, req_builder)
            print(req_builder)
        except Exception as e:
            Logger.error(e)
            errors.send_error(client, e, self.configurator)

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
            if req.insufficient():
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
            self.close(client)
        except Exception as e:
            Logger.error(f'Client handling failed', e)
            errors.send_error(client, e, self.configurator)

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
                        default=LogLevel.from_string('logging'),
                        choices=list(LogLevel))
    parser.add_argument('--server-log',
                        help='Specify server logger file path',
                        default=None)
    parser.add_argument('--debug-log',
                        help='Specify debug logger file path',
                        default=None)

    args = parser.parse_args()

    server = Server(config=args.config, loglevel=args.loglevel,
                    server_log=args.server_log,
                    debug_log=args.debug_log)
    with server as s:
        s.serve()
