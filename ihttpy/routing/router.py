import os
import re

from ihttpy.exceptions.errors import Errors
from ihttpy.requests.request import Request
from ihttpy.routing.page import Page
from ihttpy.exceptions.logger import Logger
from defenitions import ROOT_DIR, SUPPORTED_METHODS
from importlib.machinery import SourceFileLoader


class Router:
    URL_TO_RULE = {}

    def __init__(self):
        self.reg_sub = re.compile(r'(?P<txt>.*?)\[(?P<group>.*?)\]')
        self.handlers = {}

    def get_destination(self, url, rules, absolute=True):
        Logger.debug_info(f'Url processing {url}')
        for key, page in rules.items():
            path = page.get_path()

            rule = self.to_template(key)
            match = re.fullmatch(rule, url)
            if match:
                for k, v in match.groupdict().items():
                    pattern = re.compile(rf'\[{k}\]')
                    path = re.sub(pattern, v, path)

                if absolute:
                    path = self.to_abs_path(path)

                self.URL_TO_RULE[url] = key
                if os.path.isfile(path):
                    Logger.debug_info(f'Path found {path}', extra={'url': url})
                    return path
                else:
                    Logger.error(f'Path matched by rule {rule} but file not '
                                 f'found {path}', extra={'url': url})
        raise FileNotFoundError(url, rules)

    def to_abs_path(self, path):
        if not path:
            return path
        return os.path.join(ROOT_DIR, path)

    def to_template(self, key):
        key = re.sub(r'\.', r'\.', key)
        replaced = re.sub(self.reg_sub, rf'\1(?P<\2>\\w*)', key)
        reg_rep = re.compile(replaced)
        print(key, replaced, reg_rep, sep='\n')
        return reg_rep

    def get_type(self, url, rules):
        if url in self.URL_TO_RULE:
            page: Page = rules[self.URL_TO_RULE[url]]
            return page.mime

    def load_handlers(self, rules):
        for key, page in rules.items():
            path = page.get_abs_handler_path()
            if path and path not in self.handlers:
                try:
                    module = SourceFileLoader(f'{key}.handler', path)\
                        .load_module()
                    self.handlers[path] = module
                    Logger.debug_info(f'Handler {path} imported',
                                      extra={'url': page.get_path()})
                except ImportError as e:
                    Logger.exception('Handler module import failed')

    def find_page_description(self, url, rules) -> Page:
        for key, page in rules.items():
            if re.fullmatch(self.to_template(key), url):
                return page
        raise Errors.NOT_FOUND

    def find_handler(self, req: Request, rules):
        url = req.url.path

        try:
            page = self.find_page_description(url, rules)
            path = page.get_abs_handler_path()
            handler_module = self.handlers.get(path)
            if not handler_module:
                raise Errors.NO_HANDLER
            if req.method in SUPPORTED_METHODS:
                f_name = page.get_function_name_for_method(req.method)
            else:
                raise Errors.METHOD_NOT_SUPPORTED
            Logger.debug_info(f'Custom handler found: {f_name}(...) in '
                              f'{handler_module.__dict__["__file__"]}')
            return handler_module.__dict__[f_name]
        except Exception as e:
            if e == Errors.METHOD_NOT_SUPPORTED:
                raise e
            elif e == Errors.NO_HANDLER:
                Logger.debug_info(e)
                Logger.debug_info(f'Default file sender available only')
                from ihttpy.requests.sender import handle
                return handle
            else:
                raise e


