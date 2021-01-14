import json
import uuid

from backend.request import Request
from backend.response import Response

PICTURES_PATH = dict()

SUCCESS = {'status': 'success'}
FAIL = {'status': 'fail'}


def get_restaurant(req: Request, server):
    restaurant_id = req.query['id'][0]
    body = f'{json.dumps(FAIL)}'.encode()

    found = server.database.get_restaurant(restaurant_id)
    body = f'{json.dumps(found)}'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
        ["Access-Control-Allow-Origin", '*']
    ]
    return Response(200, 'OK', headers, body)


def get_picture(req: Request, server):
    req_picture = req.path[1:]
    path = PICTURES_PATH[req_picture]
    with open(path, 'rb') as f:
        to_send = f.read()
    body = to_send
    headers = [
        ('Content-Disposition', f'inline; filename={req_picture}'),
        ('Content-Length', len(body)),
        ("Access-Control-Allow-Origin", '*')
    ]
    return Response(200, 'OK', headers, body)


def get_restaurants(req: Request, server):
    restaurants = server.database.get_restaurants()
    body = (f'{json.dumps(restaurants)}'.encode())
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=restaurants'),
        ('Content-Length', len(body)),
        ["Access-Control-Allow-Origin", '*']
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
