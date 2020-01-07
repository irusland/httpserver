import email
import re
import urllib.parse
from email.message import Message

import os

import magic

from backend.errors import Errors
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
    r = re.compile(b'-+?.+?\r\n'
                   b'Content-Disposition: form-data; '
                   b'name=\"(?P<name>.*?)\"; '
                   b'filename=\"(?P<filename>.*?)\"\r\n'
                   b'.+?: (?P<ct>.+?)\r\n'
                   b'\r\n'
                   b'(?P<data>.*?)\r\n'
                   b'.+?\r\n', re.S)
    match = r.search(req.body)
    if not match:
        raise Errors.MALFORMED_REQ
    groups = match.groupdict()
    ftype = groups.get('name')
    fname = Request.decode(groups.get('filename'))
    data = groups.get('data')
    if fname:
        with open(os.path.join(ROOT_DIR, 'tmp', 'saved', fname), 'wb') as f:
            f.write(data)
        Logger.debug_info(f'{ftype} saved as {fname} ')

        body = f'{os.path.join(ROOT_DIR, "tmp", "saved")}' \
               f' - >' \
               f' {os.listdir(os.path.join(ROOT_DIR, "tmp", "saved"))}'
    else:
        body = 'Empty file'
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Echo query'),
        ('Content-Length', len(body)),
        ('Location', '/upload'),
    ]
    return Response(301, 'Moved Permanently', headers, body.encode())


def load(req: Request, server):
    filename = re.sub('/load/', '', req.target)
    destination = os.path.join(ROOT_DIR, "tmp", "saved",
                               urllib.parse.unquote(filename))
    content_type = magic.Magic(mime=True).from_file(destination)
    res = Response.build_file_res(
        req, destination, content_type)
    return res
