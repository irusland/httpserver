import json
from urllib.parse import parse_qs

from package.backend.requests.request import Request
from package.backend.response import Response

POSTS = [{"username": "Ruslan", "post": "Post"}]


def get_posts(req: Request, server):
    body = f'{json.dumps(POSTS)}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
    ]
    return Response(200, 'OK', headers, body)


def handle_post(req: Request, server):
    req.body_file.seek(0)
    body = req.body_file.read()
    body = Request.decode(body)
    query = parse_qs(f'{body}')
    POSTS.append(query)
    body = f'POST ADDED {query}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Post'),
        ('Content-Length', len(body)),
        ('Location', '/my_guest_book'),
    ]
    return Response(301, 'Moved Permanently', headers, body)
