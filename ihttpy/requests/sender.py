import urllib

import magic

from ihttpy.exceptions.errors import Errors
from ihttpy.exceptions.logger import Logger
from ihttpy.requests.request import Request
from ihttpy.requests.response import Response
from ihttpy.httpserver import Server


EXPIRE = 1


def handle(req: Request, server: Server):
    if req.path.startswith('/') and req.method == 'GET':
        rules = server.configurator._get_rules()

        path = urllib.parse.unquote(req.path)
        res = server.cache.get(path)
        if res:
            Logger.debug_info(f'Cache found for {path}')
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
            if int(res.status) == 200:
                Logger.debug_info(f'Updating cache for {path}')
                server.cache.set(path, res, expire=EXPIRE, tag='data')
                server.cache.cull()
            return res
        raise Errors.NOT_FOUND
