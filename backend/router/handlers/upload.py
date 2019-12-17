import urllib

import magic
import os

from backend.errors import Errors
from backend.logger import Logger
from backend.request import Request
from backend.response import Response
from defenitions import ROOT_DIR


def show(req: Request, server):

    res = Response.build_file_res(
        req, os.path.join(ROOT_DIR, 'tmp', 'upload.html'), 'text/html')


    body = f'{os.listdir(os.path.join(ROOT_DIR, "tmp", "saved"))}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Echo query'),
        ('Content-Length', len(body)),
    ]
    return Response(200, 'OK', headers, body)


def save(req: Request, server):
    print(req)
    body = f'{os.listdir(os.path.join(ROOT_DIR, "tmp", "saved"))}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Echo query'),
        ('Content-Length', len(body)),
    ]
    return Response(200, 'OK', headers, body)
