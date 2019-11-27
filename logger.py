import logging
from enum import Enum

from defenitions import LOGGER_PATH


class LogLevel(Enum):
    console = 0
    logging = 1
    # other_module = 2

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return LogLevel[s]
        except KeyError:
            raise ValueError()


class Logger:
    LEVEL = LogLevel.logging

    @staticmethod
    def configure(level=LogLevel.logging, path=LOGGER_PATH):
        Logger.LEVEL = level
        if Logger.LEVEL == LogLevel.logging:
            logging.basicConfig(filename=path, level=logging.INFO,
                                filemode='w+')

    @staticmethod
    def info(*args):
        if Logger.LEVEL == LogLevel.console:
            print(f'INFO: ', *args)
        elif Logger.LEVEL == LogLevel.logging:
            logging.info(*args)

    @staticmethod
    def error(*args):
        if Logger.LEVEL == LogLevel.console:
            print(f'ERROR: ', *args)
        elif Logger.LEVEL == LogLevel.logging:
            logging.error(*args)

    @staticmethod
    def exception(*args):
        if Logger.LEVEL == LogLevel.console:
            print(f'EXCEPTION: ', *args)
        elif Logger.LEVEL == LogLevel.logging:
            logging.exception(*args)
