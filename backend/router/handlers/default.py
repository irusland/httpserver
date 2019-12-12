import urllib

import magic

from backend.errors import Errors
from backend.logger import Logger
from backend.response import Response
from httpserver import Server


def handle(req, server: Server):
    if req.path.startswith('/') and req.method == 'GET':
        rules = server.configurator.get_rules()
        try:
            path = urllib.parse.unquote(req.path)
            res = server.cache.get(path)
            if res:
                Logger.info(f'Cache found for {path}')
                return res
            page = server.router.find_page_description(path, rules)
            destination = server.router.get_destination(path, rules, True)
            content_type = page.get_mime()
            if destination:
                if not content_type:
                    mime = magic.Magic(mime=True)
                    content_type = mime.from_file(destination)
                    server.cache.close()
                res = Response.build_file_res(
                    req, destination, content_type,
                    add_headers=page.get_headers())
                Logger.info(f'Updating cache for {path}')
                server.cache.set(path, res, expire=None, tag='data')
                server.cache.cull()
                return res
        except FileNotFoundError:
            raise Errors.NOT_FOUND
        raise Errors.NOT_FOUND
