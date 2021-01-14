import json
import uuid
from email.mime.text import MIMEText

import objects.user
from backend.request import Request
from backend.response import Response
from env.var import BACKEND_ADDRESS, FRONTEND_ADDRESS

from handlers import users_api, email_sender


class Order:
    def __init__(self, user, restaurant, time, comment, is_validated=False):
        self.id = uuid.uuid4().hex
        self.is_validated = is_validated
        self.validation_url = f'accept-{uuid.uuid4().hex}{uuid.uuid4().hex}'
        self.comment = comment
        self.time = time
        self.restaurant = restaurant
        self.user = user

    def __str__(self):
        return ', '.join(self.dump())

    def __repr__(self):
        return self.__str__()

    def dump(self):
        d = dict()
        for k, v in self.__dict__.items():
            o = v
            if hasattr(v, 'dump'):
                o = v.dump()
            d[k] = o
        return d


ORDERS = []


def order(req: Request, server):
    req.body_file.seek(0)
    body = req.body_file.read()
    body = Request.decode(body)
    order_data = json.loads(body)

    orderer = server.database.get_user(order_data['email'])
    if orderer:
        orderer = objects.user.User.from_dict(orderer)
    else:
        orderer = objects.user.User.from_dict(order_data)

    new_order = Order(orderer, order_data['restaurant_id'], order_data['time'],
                      order_data['comment'])
    ORDERS.append(new_order)

    address = BACKEND_ADDRESS
    link = f'http://{address}/orders/{new_order.validation_url}'
    html = f"""\
        <html>
          <body>
            <p>Hello, to confirm your reservation press 
            <a href="{link}">CONFIRM</a>
            </p>
          </body>
        </html>
        """
    mimetext = MIMEText(html, "html")
    email_sender.send(new_order.user.email, mimetext)

    body = json.dumps({
        'id': new_order.id,
        'is_validated': new_order.is_validated
    }).encode()

    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Get posts'),
        ('Content-Length', len(body)),
        ["Access-Control-Allow-Origin", '*']
    ]
    return Response(200, 'OK', headers, body)


def validate(req: Request, server):
    accept_uid = req.path.split('/')[-1]
    target_order: Order = None
    for o in ORDERS:
        if o.validation_url == accept_uid:
            if o.is_validated:
                break
            o.is_validated = True
            user = server.database.get_user(o.user.email)
            if not user:
                server.database.add_user(o.user.dump())
            break

    body = f'ok'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Post'),
        ('Content-Length', len(body)),
        ('Location', f'http://{FRONTEND_ADDRESS}/check'),
    ]
    return Response(301, 'Moved Permanently', headers, body)


def get_all(req: Request, server):
    body = json.dumps([o.dump() for o in ORDERS]).encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=json'),
        ('Content-Length', len(body)),
        ["Access-Control-Allow-Origin", '*']
    ]
    return Response(200, 'OK', headers, body)


def get_info(req: Request, server):
    order_id = req.path.split('/')[-1]
    print(order_id)
    target_order: Order = None
    for o in ORDERS:
        if o.id == order_id:
            target_order = o
            break

    body = json.dumps({'status': 'FAILED', 'reason': 'order_not_found'}).encode()
    if target_order:
        body = json.dumps(
            dict(
                filter(
                    lambda x: x[0] not in ['validation_url', '_id'],
                    target_order.dump().items()
                )
            )).encode()

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
