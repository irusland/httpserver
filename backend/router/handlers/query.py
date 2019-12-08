import urllib

import magic

from backend.errors import Errors
from backend.logger import Logger
from backend.response import Response


def handle(req, server):
    body = f'{req.query}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Echo query'),
        ('Content-Length', len(body)),
    ]
    return Response(200, 'OK', headers, body)
