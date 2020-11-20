import os
import unittest
import random

from backend import errors
from backend.configurator import Configurator
from defenitions import ROOT_DIR
from tests.defenitions import get_config
from tests.test_router import PathFinderTests
from backend.errors import Error


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
        self.cfg_path = os.path.join(ROOT_DIR, 'tests',
                                     f'cfg{random.random()}.tmp')
        with open(self.cfg_path, "w") as f:
            f.write(get_config())

        self.configurator = Configurator(self.cfg_path)
        self.rules = self.configurator.get('rules')

    def tearDown(self):
        os.remove(self.cfg_path)

    def test_empty_send(self):
        sock = SockMock()
        errors.send_error(sock, None, self.configurator)
        self.assertIsNotNone(sock.received)


if __name__ == '__main__':
    unittest.main()
