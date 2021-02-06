import json
from email.mime.text import MIMEText

from ihttpy.requests.request import Request
from ihttpy.requests.response import Response
from ihttpy.environment import BACKEND_ADDRESS, FRONTEND_ADDRESS

from ihttpy.handlers import email_sender
from database.objects.order import Order
from database.objects.user import User


def order(req: Request, server):
    req.body_file.seek(0)
    body = req.body_file.read()
    body = Request.decode(body)
    order_data = json.loads(body)

    orderer = server.database.get_user(order_data['email'])
    if orderer:
        orderer = User.from_dict(orderer)
    else:
        orderer = User.from_dict(order_data)

    new_order = Order(orderer, order_data['restaurant_id'], order_data['time'],
                      order_data['comment'])

    server.database.add_order(new_order.dump())

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
    found = server.database.get_order({'validation_url': accept_uid})
    if found and not found['is_validated']:
        server.database.update_order({'_id': found['_id']}, {'is_validated': True})

        user = server.database.get_user(found['user']['email'])
        if not user:
            server.database.add_user(
                User.from_dict(found['user']).dump())

    body = f'ok'.encode()
    headers = [
        ('Content-Type', f'application/json'),
        ('Content-Disposition', f'inline; filename=Post'),
        ('Content-Length', len(body)),
        ('Location', f'http://{FRONTEND_ADDRESS}/check'),
    ]
    return Response(301, 'Moved Permanently', headers, body)


def get_all(req: Request, server):
    orders = [o for o in server.database.get_orders()]
    body = json.dumps(orders).encode()
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
    found = server.database.get_order({'id': order_id})
    if found:
        target_order = Order.from_dict(found)

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
