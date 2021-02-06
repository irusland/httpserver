from ihttpy.requests.response import Response
from ihttpy.exceptions.logger import Logger


def send_error(connection, err, config):
    try:
        if err.page:
            with open(config.get("error-pages").get(err.page), 'rb') as p:
                p = p.read()
            res = [Response.build_err_res(err.status, err.reason, p)]
        else:
            res = [Response.build_err_res(
                err.status, err.reason,
                (err.body or err.reason).encode('utf-8'))]
    except AttributeError:
        res = [Response.build_err_res(500, b'Internal Server Error',
                                      b'Internal Server Error')]
    except Exception as e:
        Logger.error(f'Error during err creation', e)
    Response.send_response(connection, *res)
