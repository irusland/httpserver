import socket
import tempfile
import unittest

from backend.request import Request
from backend.response import Response


class SockMock:
    def __init__(self):
        self.ip = ('0.0.0.0', 8000)
        self.received = []

    def getpeername(self):
        return self.ip

    def sendall(self, args):
        self.send(args)

    def send(self, args):
        self.received.append(args)
        return len(args)


class SockMockRaiser(SockMock):
    def __init__(self):
        SockMock.__init__(self)

    def getpeername(self):
        raise socket.error(9, 'Bad file descriptor')


class SockMockSendRaiser(SockMock):
    def __init__(self):
        SockMock.__init__(self)

    def getpeername(self):
        return self.ip

    def sendall(self, args):
        self.send(args)

    def send(self, args):
        raise socket.error(32, "Broken pipe")


class TestResponse(unittest.TestCase):
    def test_mocked_res(self):
        sock = SockMock()
        res = [Response.build_err_res(1, b'Mock', b'Mock')]
        Response.send_response(sock, *res)
        self.assertIsNotNone(sock.received)

    def test_mocked_peer_raise(self):
        sock = SockMockRaiser()
        res = [Response.build_err_res(1, b'Mock', b'Mock')]
        Response.send_response(sock, *res)
        self.assertIsNotNone(sock.received)

    def test_mocked_send_raise(self):
        sock = SockMockSendRaiser()
        res = [Response.build_err_res(1, b'Mock', b'Mock')]
        self.assertRaises(socket.error, Response.send_response, *(sock, *res))

    def test_range_res(self):
        req = Request()
        req.headers['Range'] = 'bytes=0-10'
        file = tempfile.NamedTemporaryFile(mode='w+b')
        file.write(b'0123456789')
        file.seek(0)
        res = Response.build_file_res(
            req, file.name, 'text/html')
        self.assertEqual(res.status, 206)
        self.assertEqual(res.reason, 'Partial Content')
        self.assertEqual(res.headers.get('Content-Length'), 10)
        self.assertEqual(res.body, b'0123456789')

    def test_range_res_no_start(self):
        req = Request()
        req.headers['Range'] = 'bytes=-2'
        file = tempfile.NamedTemporaryFile(mode='w+b')
        file.write(b'0123456789')
        file.seek(0)
        res = Response.build_file_res(
            req, file.name, 'text/html')
        self.assertEqual(res.status, 206)
        self.assertEqual(res.reason, 'Partial Content')
        self.assertEqual(res.headers.get('Content-Length'), 2)
        self.assertEqual(res.body, b'89')

    def test_range_res_no_end(self):
        req = Request()
        req.headers['Range'] = 'bytes=9-'
        file = tempfile.NamedTemporaryFile(mode='w+b')
        file.write(b'0123456789')
        file.seek(0)
        res = Response.build_file_res(
            req, file.name, 'text/html')
        self.assertEqual(res.status, 206)
        self.assertEqual(res.reason, 'Partial Content')
        self.assertEqual(res.headers.get('Content-Length'), 1)
        self.assertEqual(res.body, b'9')


if __name__ == '__main__':
    unittest.main()
