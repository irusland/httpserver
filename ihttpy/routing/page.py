import os
import typing

from ihttpy.defenitions import SUPPORTED_METHODS
from ihttpy.requests.methods import Method


class Page:
    def __init__(self, config_description, handlers):
        self.handlers: dict[Method, typing.Callable] = handlers
        self.path = None
        self.mime = None
        self.headers = None
        self.handler_path = None
        self.func_names = {}
        if not isinstance(config_description, dict):
            self.path = config_description
            return

        self.path = config_description.get('path')
        self.mime = config_description.get('mime')
        self.headers = config_description.get('headers')

        self.handler = config_description.get('handler') or {}
        self.handler_path = self.handler.get('source')
        methods = SUPPORTED_METHODS
        for method in methods:
            self.func_names[method] = self.handler.get(method)

    def get_path(self) -> str:
        return self.path

    def get_mime(self) -> str:
        return self.mime

    def get_abs_handler_path(self) -> str:
        return self.handler_path if self.handler_path else ''

    def get_headers(self) -> list:
        return self.headers

    def get_function_name_for_method(self, method: str) -> str:
        return self.func_names.get(method.upper())

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        fields = []
        fields.append(f'\nPage with {len(self.handlers)} handlers')
        for name, value in self.__dict__.items():
            if not name.startswith('_'):
                fields.append(f'\t{name} = {value}')
        return '\n'.join(fields)

    def get_handler(self, method: Method):
        for key_method, func in self.handlers.items():
            if key_method & method:
                return func
