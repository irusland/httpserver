import json
import uuid

from ihttpy.exceptions.logger import Logger
from ihttpy.requests.request import Request
from ihttpy.requests.response import Response

TO_SEND = {"Name": "Adam", "Id": 13, "Rank": 1}

SUCCESS = {'status': 'success'}


def get(req: Request, server):
    cb_name = req.query['callback'][0]
    to_send = f'{cb_name}({json.dumps(TO_SEND)});'
    body = f'{to_send}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
        ("Access-Control-Allow-Origin", '*')
    ]
    return Response(200, 'OK', headers, body)


def img(req: Request, server):
    with open('/schema.jpg', 'rb') as f:
        to_send = f.read()
    body = to_send
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
        ("Access-Control-Allow-Origin", '*')
    ]
    return Response(200, 'OK', headers, body)


def post(req: Request, server):
    Logger.debug_info(f'POST---------')
    req.body_file.seek(0)
    body = req.body_file.read()
    body = Request.decode(body)
    Logger.debug_info(f'POSTED -> {body}')
    post_data = json.loads(body)
    BOOKS.append({
        'id': uuid.uuid4().hex,
        'title': post_data.get('title'),
        'author': post_data.get('author'),
        'read': post_data.get('read')
    })
    SUCCESS['message'] = 'Books added!'
    body = f'{json.dumps(SUCCESS)}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
        ("Access-Control-Allow-Origin", '*')
    ]
    return Response(200, 'OK', headers, body)