import json
from backend.request import Request
from backend.response import Response

POSTS = [{"username": "Ruslan", "post": "Post"}]


def get(req: Request, server):
    body = f'{json.dumps(POSTS)}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
    ]
    return Response(200, 'OK', headers, body)

