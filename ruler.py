import json
import os
import re

from defenitions import CONFIG_PATH, ROOT_DIR


class Ruler:
    PROCESSED = {}

    def __init__(self):
        pass

    def get_rules(self):
        with open(CONFIG_PATH) as cfg:
            data = json.load(cfg)
            try:
                rules = data['rules']
            except KeyError:
                return {}
            return rules

    def get_destination(self, url, raw, abs=True):
        for key, path in raw.items():
            if abs:
                path = self.to_abs_path(path)
            # else:
            #     path = os.path.join('.', path)
            template = self.to_template(key)
            match = re.match(template, url)
            if match:
                if os.path.isfile(path):
                    return path
                elif os.path.isdir(path):
                    file_path = os.path.join(path, f'{match.group("name")}.'
                                                   f'{match.group("ext")}')
                    if os.path.isfile(file_path):
                        return file_path
                raise FileNotFoundError(path, url, template, abs)

    def to_abs_path(self, path):
        return os.path.join(ROOT_DIR, path)

    def to_template(self, key):
        r = re.compile(r'(?P<p>.*/)(?P<n>.*)\.(?P<e>.*)')
        m = re.match(r, key)
        return \
            re.compile(rf'{m.group("p")}'
                       rf'(?P<name>'
                       rf'{".*" if m.group("n") == "*" else m.group("n")})'
                       rf'\.(?P<ext>'
                       rf'{".*" if m.group("e") == "*" else m.group("e")})')


if __name__ == '__main__':
    ruler = Ruler()
    r = ruler.get_rules()
    d = ruler.get_destination('/3.html', r)
    print(d)
