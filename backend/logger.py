import logging
import sys
from enum import Enum

from defenitions import LOGGER_PATH


class LogLevel(Enum):
    console = 0
    logging = 1

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        if s in LogLevel._member_map_:
            return LogLevel[s]
        raise ValueError()


class Logger:
    LEVEL = LogLevel.logging
    EXTRA = {'url': '', 'code': ''}

    @staticmethod
    def configure(level=LogLevel.logging, path=LOGGER_PATH):
        Logger.LEVEL = level
        fmt = '%(levelname)-4s: %(asctime)-15s %(url)s %(code)s %(message)s'
        if Logger.LEVEL == LogLevel.logging:
            logging.basicConfig(filename=path, level=logging.DEBUG,
                                filemode='w+', format=fmt,
                                datefmt='%m/%d/%Y %I:%M:%S')
        elif Logger.LEVEL == LogLevel.console:
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                                format=fmt, datefmt='%m/%d/%Y %I:%M:%S')

    @staticmethod
    def prepare_extra(extra=None):
        if extra is None:
            extra = {}
        res = {k: extra.get(k) if extra.get(k) is not None else ''
               for k in Logger.EXTRA.keys()}
        return res

    @staticmethod
    def info(*args, extra=None):
        logging.info(*args, extra=Logger.prepare_extra(extra))

    @staticmethod
    def error(*args, extra=None):
        logging.error(*args, extra=Logger.prepare_extra(extra))

    @staticmethod
    def exception(*args, extra=None):
        logging.exception(*args, extra=Logger.prepare_extra(extra))
