import re
import urllib.parse

import os

import magic

from package.backend.errors import Errors
from package.backend.logger import Logger
from package.backend.requests.request import Request
from package.backend.response import Response
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
    h = re.compile(b'-+?.+?\r\n'
                   b'Content-Disposition: form-data; '
                   b'name=\"(?P<name>.*?)\"; '
                   b'filename=\"(?P<filename>.*?)\"\r\n'
                   b'.+?: (?P<ct>.+?)\r\n'
                   b'\r\n', re.S)

    tail_pos = 3
    while True:
        req.body_file.seek(-tail_pos, 2)
        tail = req.body_file.tell()
        t = req.body_file.read(tail_pos)
        if t.startswith(b'\r\n'):
            break
        tail_pos += 1

    head_crlf_count = 4
    head = b''

    req.body_file.seek(0)
    i = 0
    while True:
        if i == head_crlf_count:
            break
        head += req.body_file.read(1)
        if head.endswith(b'\r\n'):
            i += 1

    data_start = req.body_file.tell()

    match = h.search(head)
    if not match:
        raise Errors.MALFORMED_REQ
    groups = match.groupdict()
    ftype = groups.get('name')
    fname = Request.decode(groups.get('filename'))
    if fname:
        with open(os.path.join(ROOT_DIR, 'tmp', 'saved', fname), 'wb') as f:
            f.write(req.body_file.read(tail - data_start))
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
