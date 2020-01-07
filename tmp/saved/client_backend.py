import socket
import sys
import logging
import chardet

from backend.query import Request, Response
from defenitions import LOG_PATH


class Client:
    ENDCHARS = [b'\r\n', b'']
    LINESEP = '\r\n'
    MAX_LINE = 64 * 1024
    HTTP_PORT = 80
    HTTPS_PORT = 443

    def __init__(self, timeout=1, show_progress=False):
        self.connected = False
        self.timeout = timeout

        logging.basicConfig(filename=LOG_PATH, filemode='w+',
                            level=logging.INFO)
        socket.setdefaulttimeout(self.timeout)
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.info(f'socket created')

        self.show_progress = show_progress

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connected = False
        self.connection.close()
        return False

    def output(self, data, file=None):
        if not file:
            try:
                sys.stdout.write(data)
            except Exception:
                sys.stdout.buffer.write(data)
            logging.info('bytes printed')
        else:
            if isinstance(data, str):
                data = bytes(data, 'utf-8')
            file.write(data)
            logging.info('File written')

    def connect(self, host, port=None):
        if port is None:
            port = Client.HTTP_PORT
        try:
            self.connection.connect((host, port))
            logging.info(f'connection established to {host}:{port}')
            self.connected = True
        except ConnectionRefusedError as e:
            logging.exception(f'Connection refused error {e}')
            self.connected = False

    def request(self, req: Request, file=None):
        redir_count = 0
        while True:
            if not self.connected:
                logging.error('No connection established')
                raise ConnectionError('Not connected')
            logging.info(f'got request to send: {req}')
            try:
                self.connection.sendall(bytes(req))
            except socket.error:
                logging.exception('Send failed')
                raise
            logging.info(f'request sent {req}')
            logging.info(f'waiting for response')
            res_builder = Response(show_progress=self.show_progress)
            break_out = False
            while not break_out:
                try:
                    while not break_out:
                        line = self.connection.recv(self.MAX_LINE)
                        split = Response.split_keep_sep(line, b'\r\n')
                        for s in split:
                            logging.info(f'received {s}')
                            if res_builder.dynamic_fill(s):
                                break_out = True
                            if (not res_builder.has_redirect() or
                                    req.no_redirect or
                                    (req.max_redir and
                                     redir_count ==
                                     req.max_redir)):
                                body = res_builder.get_data_to_out()
                                if body:
                                    self.output(body, file)
                except socket.timeout:
                    logging.info(f'body not received, waiting')

            redirect = res_builder.get_redirect()
            if redirect and not req.no_redirect and \
                    (not req.max_redir or redir_count < req.max_redir):
                redir_count += 1
                req = Request('GET', redirect,
                              req.host, no_redir=req.no_redirect,
                              max_redir=req.max_redir)
            else:
                break
        return res_builder

    @staticmethod
    def decode(b):
        try:
            encoding = chardet.detect(b)['encoding']
            return str(b, encoding)
        except Exception:
            pass
        return b

    def disconnect(self):
        if self.connected:
            self.connected = False
            self.connection.close()
            logging.info(f'connection closed')
