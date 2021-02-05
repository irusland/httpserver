from functools import wraps
import random
from typing import Tuple, Any

from ihttpy.backend.requests.request import Request
from ihttpy.backend import Response
from ihttpy.backend.requests.methods import Method


supported_methods = {'GET', 'POST', 'OPTIONS'}


class Server:
    def __init__(self):
        pass

    def on(self, *methods):
        methods: set = set(methods)
        if not methods:
            methods = supported_methods
        return Config(methods)

    def run(self, address='0.0.0.0', port=8080):
        print('handling', ROUTES)
        for route, (methods, func) in ROUTES.items():
            req = Request()
            req.path = route
            flag = 2 ** random.randint(1, 4)
            method = Method(flag)
            print(method.to_simple_str(),
                  'asdasdasdasd-1o230i1239i1203i12093i123')
            if method & Method.SUPPORTED:
                req.method = method
            else:
                a = f'{flag} was not converted'
                raise Exception(a)
            print('>\n', func(req))
            print('---------------')
        pass


ROUTES: dict[str, Tuple[set[str], Any]] = {}


class Config:
    def __init__(self, methods):
        self.methods: set = methods

    def at(self, url):
        def inner(func):
            if url in ROUTES:
                methods, func = ROUTES[url]
                self.methods = self.methods.union(methods)
            ROUTES[url] = (self.methods, func)

            @wraps(func)
            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapped

        return inner

rule = Server()

# @app.route('/index').for.get.post


@rule.on(Method.GET).at('/getonly')
@rule.on(Method.GET | Method.OPTIONS).at('/')
@rule.on(Method.POST).at('/post')
def index(request: Request):
    print('<\n', request)
    return Response(200, 'OK', body=f'{request.method} ready fo'
                                    f'r {request.path}'.encode())


if __name__ == '__main__':
    rule.run(address='0.0.0.0', port=8080)
