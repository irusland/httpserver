import inspect
import os
import random
import typing

from ihttpy.requests.methods import Method
from ihttpy.requests.request import Request
from ihttpy.routing.page import Page


class FluentConfigurator:
    def __init__(self):
        self.host = None
        self.port = None
        self.rules: dict[str, Page] = {}

    def on(self, methods: Method):
        if not methods:
            methods = Method.SUPPORTED
        return ConfiguratorRouteState(self, methods)

    def get_rules(self):
        return self.rules

    def get(self, key):
        return self.__dict__[key]

    def run(self, address='0.0.0.0', port=8080):
        print('handling', self.rules)
        for route, page in self.rules.items():
            req = Request()
            req.path = route
            flag = 2 ** random.randint(0, 4)
            method = Method(flag)
            print(method.to_simple_str(),
                  route)
            if method & Method.SUPPORTED:
                req.method = method
            else:
                a = f'{flag} was not converted'
                raise Exception(a)
            handler = page.get_handler(method)
            if handler:
                print('>\n', handler(req, None))
            else:
                print('>\n', 'failed')
            print('---------------')
        pass


class ConfiguratorRouteState:
    def __init__(self, parent: FluentConfigurator, methods: Method):
        self.parent: FluentConfigurator = parent
        self.methods: Method = methods

    def at(self, url):
        def inner(func):
            handler = {
                'source': os.path.abspath(inspect.getfile(func)),
            }
            method_handlers: dict[Method, typing.Callable] = {}
            for m in self.methods:
                handler[m.to_simple_str()] = func.__name__
                method_handlers[m] = func
            desc = {
                'handler': handler
            }
            page_description = Page(desc, method_handlers)
            self.parent.rules[url] = page_description

            return func

        return inner
