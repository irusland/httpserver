from urllib.parse import urlparse, parse_qs


class Request:
    def __init__(self, method, target, version, headers, file, user):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.file = file
        self.user = user
        self.url = urlparse(self.target)
        self.path = self.url.path
        self.query = parse_qs(self.url.query)

    def __str__(self):
        return '\n'.join(f'{k}: {v}' for k, v in self.__dict__.items())

    @staticmethod
    def parsed_req_to_request(method, target,
                              ver, headers, file, peername=None):
        return Request(method, target, ver, headers, file, peername)

