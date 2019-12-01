import os
import re

from defenitions import ROOT_DIR

from logger import Logger


class PathFinder:
    URL_TO_RULE = {}

    def __init__(self):
        self.reg_sub = re.compile(r'(?P<txt>.*?)\[(?P<group>.*?)\]')

    def get_destination(self, url, rules, absolute=True):
        Logger.info(f'Path processing {url}')
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
                    Logger.info(f'Path found {path}')
                    return path
                else:
                    Logger.error(f'Path matched by rule {rule} but file not '
                                 f'found {path}')
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


if __name__ == '__main__':
    pass
    # ruler = PathFinder()
    # r = ruler.get_rules()
    # url = '/new page.html'
    # d = ruler.get_destination(url, r)
    # t = ruler.get_type(url, r)
    # print(d, t)
