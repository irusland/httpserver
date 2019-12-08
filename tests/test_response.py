import socket
import unittest

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


class SockMockRaiser:
    def __init__(self):
        self.ip = ('0.0.0.0', 8000)
        self.received = []

    def getpeername(self):
        raise socket.error(9,'Bad file descriptor')


class SockMockSendRaiser:
    def __init__(self):
        self.ip = ('0.0.0.0', 8000)
        self.received = []

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


if __name__ == '__main__':
    unittest.main()
