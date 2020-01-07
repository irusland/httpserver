import json


class Configurator:
    DEFAULT_FIELDS = ['host', 'port', 'rules', 'error-pages']

    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.config = None
        self.refresh()

    def refresh(self):
        with open(self.cfg_path) as cfg:
            config = json.load(cfg)
            self.check(config)
            self.config = config

    def get_rules(self):
        self.refresh()
        return self.get('rules')

    @staticmethod
    def check(config):
        for f in Configurator.DEFAULT_FIELDS:
            if f not in config:
                raise KeyError(f'Config parsing failed. Field {f} not found')

    def get(self, field):
        return self.config.get(field)
