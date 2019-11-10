import json
import os
import re

from defenitions import CONFIG_PATH, ROOT_DIR, LOGGER_PATH
import logging

class Ruler:
    PROCESSED = {}

    def __init__(self):
        logging.basicConfig(filename="LOGGER_PATH", level=logging.INFO)
        pass

    def get_rules(self):
        with open(CONFIG_PATH) as cfg:
            try:
                data = json.load(cfg)
                rules = data['rules']
            except KeyError as e:
                logging.error(e)
                return {}
            except Exception as e:
                logging.exception(e)
            return rules

    def get_destination(self, url, rules, absolute=True):
        for key, path in rules.items():
            if absolute:
                path = self.to_abs_path(path)
            # todo relative path
            # else:
            #     path = os.path.join('.', path)
            template = self.to_template(key)
            match = re.fullmatch(template, url)
            if match:
                if os.path.isdir(path):
                    path = os.path.join(path, f'{match["name"]}.'
                                              f'{match["ext"]}')
                # print('debug', ' match: checking file',
                #       match.groupdict(), template, url, path)
                if os.path.isfile(path):
                    return path
                raise FileNotFoundError(path, url, template, absolute)
        raise FileNotFoundError(url, rules)

    def to_abs_path(self, path):
        return os.path.join(ROOT_DIR, path)

    def to_template(self, key):
        # r_old = re.compile(r'(?P<path>.*/)(?P<name>.*)\.(?P<ext>.*)')
        reg = re.compile(r'(?:(?P<path>.*/))*(?:(?P<name>.*)\.(?P<ext>.*))*')
        match = re.match(reg, key)
        if not match["name"]:
            return re.compile(rf'(?P<path>{match["path"]})')
        return \
            re.compile(rf'(?P<path>{match["path"]})'
                       rf'(?!.*?/)'
                       rf'(?P<name>'
                       rf'{".*" if match["name"] == "*" else match["name"]})'
                       rf'\.(?P<ext>'
                       rf'{".*" if match["ext"] == "*" else match["ext"]})')


if __name__ == '__main__':
    ruler = Ruler()
    r = ruler.get_rules()
    d = ruler.get_destination('/naksdasd.py', r)
    print(d)
