import json
import uuid

from ihttpy.exceptions.logger import Logger
from ihttpy.requests.request import Request
from ihttpy.requests.response import Response

BOOKS = [
    {
        'id': uuid.uuid4().hex,
        'title': 'On the Road',
        'author': 'Jack Kerouac',
        'read': True
    },
    {
        'id': uuid.uuid4().hex,
        'title': 'Harry Potter and the Philosoapher\'s Stone',
        'author': 'J. K. Rowling',
        'read': False
    },
    {
        'id': uuid.uuid4().hex,
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


def preflight(req: Request, server):
    method = 'Access-Control-Request-Method'
    headers = 'Access-Control-Request-Headers'
    requested_method = req.headers.get(method)
    requested_headers = req.headers.get(headers)
    body = b''
    headers = [
        ('Content-Length', len(body)),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', requested_method),
        ('Access-Control-Allow-Headers', requested_headers)
    ]
    return Response(200, 'OK', headers, body)


def put(req: Request, server):
    post_data = req.get_json()
    book_id = req.path.split('/')[-1]
    remove_book(book_id)
    BOOKS.append({
        'id': uuid.uuid4().hex,
        'title': post_data.get('title'),
        'author': post_data.get('author'),
        'read': post_data.get('read')
    })
    response_object = {'status': 'success',
                       'message': 'Book updated!'}
    body = f'{json.dumps(response_object)}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
        ("Access-Control-Allow-Origin", '*')
    ]
    return Response(200, 'OK', headers, body)


def remove_book(book_id):
    for book in BOOKS:
        if book['id'] == book_id:
            BOOKS.remove(book)
            return True
    return False


def delete(req: Request, server):
    book_id = req.path.split('/')[-1]
    remove_book(book_id)
    response_object = {'status': 'success',
                       'message': 'Book deleted!'}
    body = f'{json.dumps(response_object)}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
        ("Access-Control-Allow-Origin", '*')
    ]
    return Response(200, 'OK', headers, body)
