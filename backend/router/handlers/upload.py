import email
from email.message import Message

import os

from backend.logger import Logger
from backend.request import Request
from backend.response import Response
from defenitions import ROOT_DIR
import json


def show(req: Request, server):
    res = Response.build_file_res(
        req, os.path.join(ROOT_DIR, 'tmp', 'upload.html'), 'text/html')

    dir_list = os.listdir(os.path.join(ROOT_DIR, "tmp", "saved"))
    body = f'{json.dumps(dir_list)}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Echo query'),
        ('Content-Length', len(body)),
    ]
    return Response(200, 'OK', headers, body)


def save(req: Request, server):
    # logic for saving
    print(req)
    m = (b'Content-Type: ' + req.headers.get('Content-Type').encode() +
         b'\r\n' +
         req.body)
    print(m)
    msg: Message = email.parser.BytesParser().parsebytes(m)
    for part in msg.get_payload():

        ftype = part.get_param('name', header='content-disposition')
        fname = part.get_param('filename', header='content-disposition')
        file = part.get_payload(decode=True)
        if not fname:
            Logger.debug_info(f'{ftype} is empty')
            continue
        with open(os.path.join(ROOT_DIR, 'tmp', 'saved', fname), 'wb') as f:
            f.write(file)
        Logger.debug_info(f'{ftype} saved as {fname} ')

    body = f'{os.path.join(ROOT_DIR, "tmp", "saved")}' \
           f' - >' \
           f' {os.listdir(os.path.join(ROOT_DIR, "tmp", "saved"))}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Echo query'),
        ('Content-Length', len(body)),
        ('Location', '/upload'),
    ]
    return Response(301, 'Moved Permanently', headers, body)
