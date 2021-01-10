import json
import uuid

from backend.logger import Logger
from backend.request import Request
from backend.response import Response


class User:
    def __init__(self, email, name):
        self.name = name
        self.email = email

    def dump(self):
        return self.__dict__


USERS = [
    User('ruslansirazhetdinov@gmail.com', 'Rusland'),
]
SUCCESS = {'status': 'success'}
FAIL = {'status': 'fail'}


def get(req: Request, server):
    email = req.query['email'][0]
    print(email)

    body = f'{json.dumps(FAIL)}'.encode()
    for i, user in enumerate(USERS):
        if user.email == email:
            SUCCESS.update({'name': user.name})
            body = f'{json.dumps(SUCCESS)}'.encode()
            break

    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
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
