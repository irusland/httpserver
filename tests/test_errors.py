import unittest

from errors import Error


class SockMock:
    def __init__(self):
        self.ip = ('0.0.0.0', 8000)
        self.received = []

    def getpeername(self):
        return self.ip

    def send(self, args):
        self.received.append(args)
        return len(args)


class TestErrorsWithMock(unittest.TestCase):
    def test_empty_send(self):
        sock = SockMock()
        Error.send_error(sock, None)
        self.assertIsNotNone(sock.received)
        # print(sock.received)


if __name__ == '__main__':
    unittest.main()
