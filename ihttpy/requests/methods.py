from flags import Flags


class BaseFlags(Flags):
    __no_flags_name__ = 'NONE'
    __all_flags_name__ = 'SUPPORTED'


class Method(BaseFlags):
    GET = 1
    POST = 2
    OPTIONS = 4
    PUT = 8
    DELETE = 16
