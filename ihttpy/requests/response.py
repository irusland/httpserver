import os
import socket
import time
from collections import OrderedDict

from ihttpy.exceptions.logger import Logger


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = OrderedDict(headers or {})
        self.body = body

    def __str__(self):
        lim = 500
        return '\n'.join(
            f'{k}: {str(v)[:lim]}'
            for k, v in self.__dict__.items())

    @staticmethod
    def build_err_res(status, reason, body, css=False):
        return Response(
            status, reason,
            OrderedDict([('Content-Type', f'text/{"css" if css else "html"}'),
                         ('Content-Length', len(body))]), body)

    @staticmethod
    def build_file_res(req, path, content_type, add_headers=None):
        connection = req.headers.get('Connection')
        start, end, size = None, None, None

        range_header = req.headers.get('Range')
        with open(path, 'rb') as file:
            if range_header:
                _, v = range_header.split('=')
                start, end = v.split('-', maxsplit=1)
                if not end:
                    end = os.path.getsize(path)
                if not start:
                    start = int(end)
                    end = os.path.getsize(path)
                    start = end - start
                start, end = int(start), int(end)
                file.seek(start, 0)
                body = file.read(end - start)
            else:
                body = file.read()
        filename = os.path.basename(path)
        headers = {('Content-Type', f'{content_type}'),
                   ('Content-Disposition', f'inline; filename={filename}'),
                   ('Content-Length', len(body)), ('Connection', connection)}
        if range_header:
            headers.add(('Content-Range',
                         f'{start}-{end}/{os.stat(path).st_size}'))
        headers = OrderedDict(headers)

        for (name, value) in add_headers or []:
            headers[name] = value
        if range_header:
            return Response(206, 'Partial Content', headers, body)
        return Response(200, 'OK', headers, body)

    def headers_to_str(self):
        return ''.join(f'{k}: {v}\r\n' for (k, v) in self.headers.items())

    def status_to_str(self):
        return f'HTTP/1.1 {self.status} {self.reason}\r\n'

    @staticmethod
    def send_response(client, *res):
        try:
            ip = client.getpeername()
        except socket.error as e:
            if e.errno == 9:
                Logger.error(f'Connection with client broken')
            return

        for response in res:
            contents = b''.join((
                response.status_to_str().encode('utf-8'),
                response.headers_to_str().encode('utf-8'),
                b'\r\n',
                response.body or b''
            ))
            while contents:
                try:
                    bytes_sent = client.send(contents)
                    contents = contents[bytes_sent:]
                    Logger.debug_info(f'{bytes_sent}B sent to {ip}')
                except socket.error as e:
                    if e.errno == 35:
                        Logger.error(
                            'Resource temporarily unavailable Sleeping')
                        time.sleep(0.1)
                    elif e.errno == 32:
                        msg = f'client stopped receiving'
                        Logger.error(msg)
                        raise
                    elif e.errno == 9:
                        Logger.error(f'Connection with client {ip} broken')
                        raise
            Logger.debug_info(f'All Files sent to {ip}')
