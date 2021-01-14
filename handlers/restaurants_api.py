import json
import uuid

from backend.logger import Logger
from backend.request import Request
from backend.response import Response

from env.var import BACKEND_ADDRESS


class Restaurant:
    def __init__(self,
                 id,
                 address,
                 description,
                 working_hours,
                 pictures=None,
                 available=True):
        self.working_hours = working_hours
        self.id = id
        self.address = address
        self.description = description
        self.pictures = []
        if pictures:
            self.pictures = pictures
        self.available = available

    SHORT = ['id', 'address', 'available']

    def dump(self):
        return {key: self.__dict__[key] for key in self.SHORT}

    def dump_all(self):
        d = self.dump()
        d['description'] = self.description
        d['pictures'] = self.dump_pictures()
        d['working_hours'] = self.working_hours
        return d

    def dump_pictures(self):
        paths = []
        for path in self.pictures:
            if path.startswith('http'):
                # direct picture link
                url = path
            else:
                # server picture link
                local_path = f'restaurants/{uuid.uuid4().hex}{uuid.uuid4().hex}'
                url = f'http://{BACKEND_ADDRESS}/{local_path}'
                PICTURES_PATH[local_path] = path
            paths.append(url)
        return paths


PICTURES_PATH = dict()

RESTAURANTS = [
    Restaurant(uuid.uuid4().hex,
               'Волотильстакая 1',
               'Restaurant description ...',
               ('00:00', '23:00'),
               ['https://www.hot-dinners.com/images/stories/blog/2019/pictureteam.jpg',
                'source/picutres/restaurant.png',
                'source/picutres/rest1.png']),
    Restaurant(uuid.uuid4().hex,
               'Ленина 51',
               'Restaurant description ...',
               ('11:00', '23:00')),
    Restaurant(uuid.uuid4().hex,
               'Московская 13',
               'Restaurant description ...',
               ('10:00', '18:00'),
               available=False),
]

SUCCESS = {'status': 'success'}
FAIL = {'status': 'fail'}


def get_restaurant(req: Request, server):
    restaurant_id = req.query['id'][0]
    body = f'{json.dumps(FAIL)}'.encode()
    for restaurant in RESTAURANTS:
        if restaurant_id == restaurant.id:
            body = f'{json.dumps(restaurant.dump_all())}'.encode()
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
    body = (f'{json.dumps(list(map(lambda x: x.dump(), RESTAURANTS)))}'.encode())
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
