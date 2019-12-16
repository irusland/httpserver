import os
import socket
import time
from collections import OrderedDict

from backend.logger import Logger


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = OrderedDict(headers)
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
        accept = req.headers.get('Accept')
        connection = req.headers.get('Connection')
        if content_type in accept or '*/*' in accept:
            with open(path, 'rb') as file:
                body = file.read()
        else:
            return Response(406, 'Not Acceptable')
        filename = os.path.basename(path)
        headers = {('Content-Type', f'{content_type}'),
                   ('Content-Disposition', f'inline; filename={filename}'),
                   ('Content-Length', len(body)), ('Connection', connection)}

        headers = OrderedDict(headers)

        for (name, value) in add_headers or []:
            headers[name] = value
        #
        # visited = {name for (name, value) in add_headers or []}
        # joined_headers = add_headers or []
        # for a, b in headers:
        #     if a not in visited:
        #         visited.add(a)
        #         joined_headers.append((a, b))
        return Response(200, 'OK', headers, body)

    @staticmethod
    def headers_to_str(res):
        headers: OrderedDict = res.headers
        return ''.join(f'{k}: {v}\r\n' for (k, v) in headers.items())

    @staticmethod
    def status_to_str(res):
        return f'HTTP/1.1 {res.status} {res.reason}\r\n'

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
                Response.status_to_str(response).encode('utf-8'),
                Response.headers_to_str(response).encode('utf-8'),
                b'\r\n',
                response.body
            ))
            try:
                while contents:
                    try:
                        bytes_sent = client.send(contents)
                        contents = contents[bytes_sent:]
                        Logger.info(f'{bytes_sent}B sent to {ip}')
                    except socket.error as e:
                        if e.errno == 35:
                            Logger.error(
                                'Resource temporarily unavailable Sleeping')
                            time.sleep(0.1)
                        elif e.errno == 32:
                            msg = f'client stopped receiving {e}'
                            Logger.exception(msg)
                            raise
                        elif e.errno == 9:
                            Logger.error(f'Connection with client {ip} broken')
                            raise
            except Exception:
                raise
            else:
                Logger.info(f'Files sent to {ip}')
