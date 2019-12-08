import argparse

from backend.logger import LogLevel
from defenitions import CONFIG_PATH, LOGGER_PATH


class ArgParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-c', '--config',
                                 help='Specify server config path',
                                 default=CONFIG_PATH)
        self.parser.add_argument('-l', '--loglevel',
                                 help='Use module to write logs',
                                 type=LogLevel.from_string,
                                 default=LogLevel.from_string('console'),
                                 choices=list(LogLevel))

        self.parser.add_argument('--log-path',
                                 help='Specify logger file path',
                                 default=LOGGER_PATH)

    def parse_args(self):
        return self.parser.parse_args()
