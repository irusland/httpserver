import os

from defenitions import ROOT_DIR, SUPPORTED_METHODS


class Page:
    def __init__(self, config_description):
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

        handler = config_description.get('handler') or {}
        self.handler_path = handler.get('source')
        methods = SUPPORTED_METHODS
        for method in methods:
            method = method.lower()
            self.func_names[method] = handler.get(method)

    def get_path(self) -> str:
        return self.path

    def get_mime(self) -> str:
        return self.mime

    def get_abs_handler_path(self) -> str:
        return os.path.join(ROOT_DIR, self.handler_path) if \
            self.handler_path else ''

    def get_headers(self) -> list:
        return self.headers

    def get_function_name_for_method(self, method: str) -> str:
        return self.func_names.get(method.lower())
