import os
import re
import importlib

from defenitions import ROOT_DIR, REQUEST_HANDLERS_DIR

from backend.logger import Logger


class Router:
    URL_TO_RULE = {}

    def __init__(self):
        self.reg_sub = re.compile(r'(?P<txt>.*?)\[(?P<group>.*?)\]')

    def get_destination(self, url, rules, absolute=True):
        Logger.info(f'Path processing', extra={'url': url})
        for key, description in rules.items():
            if 'path' in description:
                path = description['path']
            else:
                path = description

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

    def find_handler(self, req):
        path = req.url.path[1:]
        import imp
        try:
            with open(os.path.join(REQUEST_HANDLERS_DIR, f'{path}.py'),
                      'rb') as fp:
                handle = imp.load_module(
                    f'{path}', fp, f'{path}.py',
                    ('.py', 'rb', imp.PY_SOURCE)
                ).handle
        except Exception:
            handle = None
        if not handle:
            name = 'default'
            with open(os.path.join(REQUEST_HANDLERS_DIR, f'{name}.py'),
                      'rb') as fp:
                handle = imp.load_module(
                    f'{name}', fp, f'{name}.py',
                    ('.py', 'rb', imp.PY_SOURCE)
                ).handle
        return handle


if __name__ == '__main__':
    pass
