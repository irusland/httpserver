import json
import os
import re

from defenitions import CONFIG_PATH, ROOT_DIR, LOGGER_PATH
import logging


class PathFinder:
    URL_TO_RULE = {}

    def __init__(self):
        logging.basicConfig(filename=LOGGER_PATH, level=logging.INFO)
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
        logging.info(f'Path processing {url}')
        for key, description in rules.items():
            try:
                path = description['path']
            except Exception:
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
                    logging.info(f'Path found {path}')
                    return path
        raise FileNotFoundError(url, rules)

    def to_abs_path(self, path):
        return os.path.join(ROOT_DIR, path)

    def to_template(self, key):
        key = re.sub(r'\.', r'\.', key)
        reg_sub = re.compile(r'(?P<txt>.*?)\[(?P<group>.*?)\]')
        replaced = re.sub(reg_sub, rf'\1(?P<\2>.*)', key)
        reg_rep = re.compile(replaced)
        return reg_rep

    def get_type(self, url, rules):
        if url in self.URL_TO_RULE:
            description = rules[self.URL_TO_RULE[url]]
            if not isinstance(description, str):
                try:
                    return description['mime']
                except KeyError:
                    return None


if __name__ == '__main__':
    pass
    # ruler = Ruler()
    # r = ruler.get_rules()
    # url = '/page-load-errors.css'
    # d = ruler.get_destination(url, r)
    # t = ruler.get_type(url, r)
    # print(d, t)
