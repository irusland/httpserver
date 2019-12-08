import urllib

import magic

from backend.errors import Errors
from backend.logger import Logger
from backend.response import Response


def handle(req, server):
    if req.path.startswith('/') and req.method == 'GET':
        rules = server.configurator.get_rules()
        try:
            path = urllib.parse.unquote(req.path)
            res = server.cache.get(path)
            if res:
                Logger.info(f'Cache found for {path}')
                return res
            destination = server.router.get_destination(path, rules, True)
        except FileNotFoundError:
            raise Errors.NOT_FOUND
        if destination:
            content_type = server.router.get_type(req.path, rules)
            if not content_type:
                mime = magic.Magic(mime=True)
                content_type = mime.from_file(destination)
                server.cache.close()
            res = Response.build_file_res(req, destination, content_type)
            Logger.info(f'Updating cache for {path}')
            server.cache.set(path, res, expire=None, tag='data')
            server.cache.cull()
            return res
        raise Errors.NOT_FOUND
