import os
import unittest
import random

from ihttpy.exceptions import send_error
from ihttpy.routing.configurator import Configurator
from tests.defenitions_for_test import TESTS_DIR
from tests.defenitions_for_test import get_config


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


class TestErrorsWithMock(unittest.TestCase):
    def setUp(self):
        self.cfg_path = os.path.join(TESTS_DIR, f'cfg{random.random()}.tmp')
        with open(self.cfg_path, "w") as f:
            f.write(get_config())

        self.configurator = Configurator(self.cfg_path)
        self.rules = self.configurator.get('rules')

    def tearDown(self):
        os.remove(self.cfg_path)

    def test_empty_send(self):
        sock = SockMock()
        send_error(sock, None, self.configurator)
        self.assertIsNotNone(sock.received)


if __name__ == '__main__':
    unittest.main()
