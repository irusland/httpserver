import os
import re

from backend.errors import Errors
from backend.request import Request
from backend.router.page import Page
from defenitions import ROOT_DIR, REQUEST_HANDLERS_DIR
from importlib.machinery import SourceFileLoader

from backend.logger import Logger


class Router:
    URL_TO_RULE = {}

    def __init__(self):
        self.reg_sub = re.compile(r'(?P<txt>.*?)\[(?P<group>.*?)\]')
        self.handlers = {}

    def get_destination(self, url, rules, absolute=True):
        Logger.info(f'Path processing', extra={'url': url})
        for key, description in rules.items():
            page = Page(description)
            path = page.get_path()

            rule = self.to_template(key)
            match = re.fullmatch(rule, url)
            if match:
                for k, v in match.groupdict().items():
                    pattern = re.compile(rf'\[{k}\]')
                    path = re.sub(pattern, v, path)

                if absolute:
                    path = self.to_abs_path(path)
                # todo relative path
                # else:
                #     path = os.path.join('.', path)

                self.URL_TO_RULE[url] = key
                if os.path.isfile(path):
                    Logger.info(f'Path found {path}', extra={'url': url})
                    return path
                else:
                    Logger.error(f'Path matched by rule {rule} but file not '
                                 f'found {path}', extra={'url': url})
        raise FileNotFoundError(url, rules)

    def to_abs_path(self, path):
        return os.path.join(ROOT_DIR, path)

    def to_template(self, key):
        key = re.sub(r'\.', r'\.', key)
        replaced = re.sub(self.reg_sub, rf'\1(?P<\2>.*)', key)
        reg_rep = re.compile(replaced)
        return reg_rep

    def get_type(self, url, rules):
        if url in self.URL_TO_RULE:
            description = rules[self.URL_TO_RULE[url]]
            if isinstance(description, dict):
                return description.get('mime')

    def load_handlers(self, rules):
        for key, description in rules.items():
            page = Page(description)
            path = page.get_handler_path()
            if path and path not in self.handlers:
                try:
                    module = SourceFileLoader(
                        f'{key}.handler', path).load_module()
                    self.handlers[path] = module
                    Logger.info(f'Handler {path} imported',
                                extra={'url': page.get_path()})
                except ImportError as e:
                    Logger.error('Handler module import failed', e)

    def find_page_description(self, url, rules):
        for key, description in rules.items():
            if re.fullmatch(self.to_template(key), url):
                return Page(description)
        raise FileNotFoundError(url, rules)

    def find_handler(self, req: Request, rules):
        url = req.url.path

        try:
            page = self.find_page_description(url, rules)
            path = page.get_handler_path()
            handler_module = self.handlers.get(path)
            if req.method == 'GET':
                f_name = page.get_get_func_name()
            elif req.method == 'POST':
                f_name = page.get_post_func_name()
            else:
                raise Errors.METHOD_NOT_SUPPORTED
            return handler_module.__dict__[f_name]
        except Exception as e:
            print(e)
            # No handler for page using default
            module = SourceFileLoader(
                f'default.handler',
                os.path.join(
                    REQUEST_HANDLERS_DIR,
                    f'default.py')).load_module()
            return module.handle


if __name__ == '__main__':
    pass
