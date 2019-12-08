import json


class Configurator:
    DEFAULT_FIELDS = ['host', 'port', 'rules', 'error-pages']
    cfg_path = None
    config = None

    @staticmethod
    def init(cfg_path):
        Configurator.cfg_path = cfg_path
        Configurator.config = Configurator.refresh(Configurator.cfg_path)
        return Configurator

    @staticmethod
    def refresh(cfg_path):
        with open(cfg_path) as cfg:
            config = json.load(cfg)
            Configurator.check(config)
            return config

    @staticmethod
    def get_rules():
        Configurator.config = Configurator.refresh(Configurator.cfg_path)
        return Configurator.get('rules')

    @staticmethod
    def check(config):
        for f in Configurator.DEFAULT_FIELDS:
            if f not in config:
                raise KeyError(f'Config parsing failed. Field {f} not found')

    @staticmethod
    def get(field):
        return Configurator.config.get(field)


class Getter:
    def __init__(self, path):
        self.path = path

    def getpath(self):
        return self.path


if __name__ == '__main__':
    pass
