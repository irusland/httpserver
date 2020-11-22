import json

from backend.logger import Logger
from backend.request import Request
from backend.response import Response

BOOKS = [
    {
        'title': 'On the Road',
        'author': 'Jack Kerouac',
        'read': True
    },
    {
        'title': 'Harry Potter and the Philosopher\'s Stone',
        'author': 'J. K. Rowling',
        'read': False
    },
    {
        'title': 'Green Eggs and Ham',
        'author': 'Dr. Seuss',
        'read': True
    }
]

SUCCESS = {'status': 'success'}


def get(req: Request, server):
    Logger.debug_info('GET----------------------------------')
    SUCCESS['books'] = BOOKS
    body = f'{json.dumps(SUCCESS)}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
        ("Access-Control-Allow-Origin", "http://localhost:8080")
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
        ("Access-Control-Allow-Origin", "http://localhost:8080")
    ]
    return Response(200, 'OK', headers, body)


def preflight(req: Request, server):
    method = 'Access-Control-Request-Method'
    headers = 'Access-Control-Request-Headers'
    requested_method = req.headers.get(method)
    requested_headers = req.headers.get(headers)
    body = b''
    headers = [
        ('Content-Length', len(body)),
        ("Access-Control-Allow-Origin", "http://localhost:8080"),
        ('Access-Control-Allow-Method', requested_method),
        ('Access-Control-Allow-Headers', requested_headers)
    ]
    return Response(200, 'OK', headers, body)
