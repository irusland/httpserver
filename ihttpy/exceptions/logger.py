import logging
import sys
from enum import Enum


class LogLevel(Enum):
    CONSOLE = 0
    LOGGING = 1

    def __str__(self):
        return self.name.lower()

    @staticmethod
    def from_string(s: str):
        s = s.upper()
        if s in LogLevel._member_map_:
            return LogLevel[s]
        raise ValueError(s)


class Logger:
    LEVEL = LogLevel.LOGGING
    EXTRA = {'url', 'code', 'method', 'ip'}
    INFO_LOGGER: logging.Logger = None
    DEBUG_LOGGER: logging.Logger = None

    @staticmethod
    def setup_logger(name, log_file, level=logging.INFO,
                     fmt='%(levelname)-4s: %(message)s',
                     datefmt='%m/%d/%Y %I:%M:%S') -> logging.Logger:

        logger = logging.getLogger(name)
        logger.setLevel(level)
        handler = None

        if Logger.LEVEL == LogLevel.LOGGING or log_file:
            if log_file:
                handler = logging.FileHandler(log_file, mode='w+')
                formater = logging.Formatter(fmt=fmt, datefmt=datefmt)
                handler.setFormatter(formater)
            else:
                return
        elif Logger.LEVEL == LogLevel.CONSOLE:
            handler = logging.StreamHandler(stream=sys.stdout)
            formater = logging.Formatter(fmt=fmt, datefmt=datefmt)
            handler.setFormatter(formater)

        logger.addHandler(handler)
        return logger

    @staticmethod
    def configure(level=LogLevel.LOGGING, info_path=None,
                  debug_path=None):
        Logger.LEVEL = level
        info_fmt = ('[%(asctime)-15s] '
                    '<%(method)s> "%(url)s" (%(code)s) '
                    '"%(ip)s" "%(message)s"')

        Logger.INFO_LOGGER = Logger.setup_logger(
            'info_logger', info_path, logging.INFO, info_fmt)

        Logger.DEBUG_LOGGER = Logger.setup_logger(
            'debug_logger', debug_path, logging.DEBUG)

    @staticmethod
    def prepare_extra(extra=None):
        if extra is None:
            extra = {}
        res = {k: extra.get(k) if extra.get(k) is not None else ''
               for k in Logger.EXTRA}
        return res

    @staticmethod
    def info(*args, extra=None):
        if Logger.INFO_LOGGER:
            Logger.INFO_LOGGER.info(*args, extra=Logger.prepare_extra(extra))

    @staticmethod
    def debug_info(*args, extra=None):
        if Logger.DEBUG_LOGGER:
            Logger.DEBUG_LOGGER.info(*args, extra=Logger.prepare_extra(extra))

    @staticmethod
    def error(*args, extra=None):
        if Logger.DEBUG_LOGGER:
            Logger.DEBUG_LOGGER.error(args, extra=Logger.prepare_extra(extra))

    @staticmethod
    def exception(args, extra=None):
        if Logger.DEBUG_LOGGER:
            Logger.DEBUG_LOGGER.exception(args,
                                          extra=Logger.prepare_extra(extra))

    # todo warn
