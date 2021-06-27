import inspect
import json
import os
import sys
import typing
from typing import Callable

import ihttpy.httpserver as srv
from ihttpy.requests.methods import Method
from ihttpy.requests.request import Request
from ihttpy.routing.page import Page
from ihttpy.utils import deprecated_after


class Configurator:
    DEFAULT_FIELDS = ['_host', '_port', 'rules', 'error-pages']

    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.config = None
        self.rules: dict[str, Page] = {}
        self.refresh()

    def refresh(self):
        with open(self.cfg_path) as cfg:
            config = json.load(cfg)
            self.check(config)
            self.config = config
            for route, description in self.config.get('rules').items():
                self.rules[route] = Page(description, {})

    def _get_rules(self):
        return self.rules

    @staticmethod
    def check(config):
        for f in Configurator.DEFAULT_FIELDS:
            if f not in config:
                raise KeyError(f'Config parsing failed. Field {f} not found')

    def get(self, field):
        return self.config.get(field)


class FluentConfigurator:
    def __init__(self):
        if sys.version_info < (3, 9):
            raise RuntimeError("Python >=3.9 needed for Fluent "
                               "configuration But your version is "
                               f"{sys.version_info}")
        self._host = None
        self._port = None
        self._rules: dict[str, Page] = {}

    def on(self, methods: Method):
        if not methods:
            methods = Method.SUPPORTED
        return ConfiguratorRouteState(self, methods)

    def _get_rules(self):
        return self._rules

    def get(self, key):
        return self.__dict__[key]


class ConfiguratorRouteState:
    def __init__(self, parent: FluentConfigurator, methods: Method):
        self.__parent__: FluentConfigurator = parent
        self._methods: Method = methods

    def at(self, url):
        def inner(func):
            page = self.__parent__._rules.get(url)
            if page:
                for m in self._methods:
                    page.handler[m.to_simple_str()] = func.__name__
                    page.handlers[m] = func
                    page.func_names[m.to_simple_str()] = func.__name__
            else:
                handler = {
                    'source': os.path.abspath(inspect.getfile(func)),
                }
                method_handlers: dict[Method, typing.Callable] = {}
                for m in self._methods:
                    handler[m.to_simple_str()] = func.__name__
                    method_handlers[m] = func
                desc = {
                    'handler': handler
                }
                page_description = Page(desc, method_handlers)
                self.__parent__._rules[url] = page_description

            return func

        return inner


class DecorativeConfigurator:
    @deprecated_after(3, 9)
    def __init__(self):
        self._host = None
        self._port = None
        self._rules: dict[str, Page] = {}

    def rule(self, methods: Method, url: str) -> Callable[
        [Callable[[Request, srv.Server], None]], Callable[
            [Request, srv.Server], None]]:
        if not methods:
            methods = Method.SUPPORTED

        def inner(func: Callable[[Request, srv.Server], None]) -> Callable[
            [Request, srv.Server], None]:
            page = self._rules.get(url)
            if page:
                for m in methods:
                    page.handler[m.to_simple_str()] = func.__name__
                    page.handlers[m] = func
                    page.func_names[m.to_simple_str()] = func.__name__
            else:
                handler = {
                    'source': os.path.abspath(inspect.getfile(func)),
                }
                method_handlers: dict[Method, typing.Callable] = {}
                for m in methods:
                    handler[m.to_simple_str()] = func.__name__
                    method_handlers[m] = func
                desc = {
                    'handler': handler
                }
                page_description = Page(desc, method_handlers)
                self._rules[url] = page_description

            return func

        return inner

    def _get_rules(self):
        return self._rules

    def get(self, key):
        return self.__dict__[key]
