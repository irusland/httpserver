import functools
import sys
import warnings


def deprecated_after(major: int, minor: int = 0, micro: int = 0):
    if sys.version_info < (major, minor, micro):
        def inner(func):
            return func
    else:
        def inner(func):
            @functools.wraps(func)
            def new_func(*args, **kwargs):
                warnings.simplefilter('always', DeprecationWarning)
                msg = (
                    f'{func.__name__} was deprecated after python'
                    f'{".".join(map(str, (major, minor, micro)))}'
                )
                warnings.warn(msg, category=DeprecationWarning)
                warnings.simplefilter('default', DeprecationWarning)
                return func(*args, **kwargs)
            return new_func
    return inner
