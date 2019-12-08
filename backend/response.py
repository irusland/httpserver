import os
import socket
import time

from backend.logger import Logger


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
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
            [('Content-Type', f'text/{"css" if css else "html"}'),
             ('Content-Length', len(body))], body)

    @staticmethod
    def build_res(req, path, content_type):
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

    @staticmethod
    def headers_to_str(res):
        return ''.join(f'{k}: {v}\r\n' for (k, v) in res.headers)

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
                client.sendall(contents)
            except socket.error as e:
                if e.errno == 35:
                    Logger.error('Resource temporarily unavailable Sleeping')
                    time.sleep(0.1)
                elif e.errno == 32:
                    msg = f'client stopped receiving {e}'
                    Logger.exception(msg)
                    raise e
                elif e.errno == 9:
                    Logger.error(f'Connection with client {ip} broken')
                    raise e
            else:
                Logger.info(f'Files sent to {ip}')
