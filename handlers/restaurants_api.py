import json
import uuid

from backend.logger import Logger
from backend.request import Request
from backend.response import Response


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
            url = f'restaurants/{uuid.uuid4().hex}{uuid.uuid4().hex}'
            PICTURES_PATH[url] = path
            paths.append(url)
        return paths


PICTURES_PATH = dict()

RESTAURANTS = [
    Restaurant(uuid.uuid4().hex,
               'Волотильстакая 1',
               'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla consequat tellus vitae porta cursus. Mauris at elit tempor, porta purus sed, tincidunt nisl. Phasellus scelerisque eleifend odio eu scelerisque. Morbi dapibus nulla urna, quis porta nisl varius sed. Mauris euismod sed urna quis auctor. Nam laoreet risus in mollis vestibulum. Sed gravida libero at fringilla ultrices. Nullam viverra diam at dolor sagittis, eget tempor nunc finibus. Vivamus facilisis ullamcorper sem, vitae laoreet neque sollicitudin a. Vivamus pellentesque magna nisi, eget molestie sapien vulputate in. Curabitur dictum turpis ac odio rutrum elementum. Curabitur at nisl odio. Cras eu hendrerit neque.',
               ('00:00', '23:00'),
               ['source/picutres/restaurant.png',
                'source/picutres/rest1.png']),
    Restaurant(uuid.uuid4().hex,
               'Ленина 51',
               'In aliquam odio in augue commodo lacinia. Donec id diam eget urna sagittis dignissim. Aliquam vehicula mauris ut odio condimentum, ut elementum urna eleifend. Mauris vel bibendum neque. Integer in pretium mauris. Sed metus nibh, semper vitae velit quis, molestie elementum nunc. Duis tincidunt facilisis tortor, at consectetur eros hendrerit in. Vivamus ullamcorper tempor sapien. Maecenas ultrices quam leo, vitae volutpat metus dapibus vitae. Quisque condimentum id velit ac vestibulum. Sed efficitur ante vel augue viverra vestibulum. Donec luctus lorem nisl. Vestibulum tristique dui quis erat consequat, non pulvinar ante dapibus. Etiam eget tortor quis nisl iaculis tincidunt. Duis sodales, nunc eu cursus consequat, justo lacus finibus sapien, non iaculis erat nunc vulputate nibh. Sed venenatis quam velit, et posuere nunc scelerisque sed.',
               ('11:00', '23:00')),
    Restaurant(uuid.uuid4().hex,
               'Московская 13',
               'Мск',
               ('10:00', '18:00'),
               None,
               False),
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
