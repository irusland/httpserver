import json


class Configurator:
    DEFAULT_FIELDS = ['host', 'port', 'rules', 'error-pages']

    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.config = self.refresh(self.cfg_path)

    def refresh(self, cfg_path):
        with open(cfg_path) as cfg:
            raw = cfg
            config = json.load(raw)
            self.check(config)
            return config

    def get_rules(self):
        self.config = self.refresh(self.cfg_path)
        return self.get('rules')

    def check(self, config):
        for f in self.DEFAULT_FIELDS:
            try:
                config[f]
            except Exception:
                raise Exception(f'Config parsing failed. Field {f} not found')

    def get(self, field):
        try:
            return self.config[field]
        except Exception:
            return None
