import os


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
