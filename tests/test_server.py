import io
import json
import multiprocessing
import os
import socket
import unittest
import random

from backend.configurator import Configurator
from defenitions import CONFIG_PATH, ROOT_DIR
from backend.logger import LogLevel
from backend.request import Request
from backend.stopper import AsyncStopper
from httpserver import Server
from tests.test_router import PathFinderTests


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.cfg_path = os.path.join(ROOT_DIR, 'tests',
                                     f'cfg{random.random()}.tmp')
        with open(self.cfg_path, "w") as f:
            f.write(PathFinderTests.CONFIG)

        self.configurator = Configurator.init(self.cfg_path)
        self.rules = self.configurator.get('rules')

    def tearDown(self):
        os.remove(self.cfg_path)

    def boot_server(self):
        server = self.make_server()
        with server as s:
            s.serve()

    def make_server(self):
        from httpserver import Server
        return Server(config=self.cfg_path, loglevel=LogLevel.CONSOLE)

    def process_req(self, req):
        with self.make_server() as server:
            file = io.BytesIO(req.encode('utf-8'))
            return server.parse_req_file(file)

    def req_to_str(self, method, target, ver, headers, body):
        return '\n'.join((
            ' '.join((method, target, ver)),
            '\n'.join(f'{k}: {v}' for k, v in headers.items()),
            f'\n{body}'))

    def assert_req_parsed(self, m, t, v, h, b):
        req = self.req_to_str(m, t, v, h, b)
        p = self.process_req(req)
        method, target, ver, headers, body = p
        self.assertTupleEqual((m, t, v), (method, target, ver))
        for k in h.keys():
            self.assertEqual(headers.get(k), h.get(k))
        self.assertEqual(b.encode(), body)

    def test_req_parsing(self):
        self.assert_req_parsed('GET', '/2.html', 'HTTP/1.1',
                               {'Host': '0.0.0.0:8000',
                                'Accept': 'text/html'}, 'body')

    def test_get_res(self):
        line = (b'GET / HTTP/1.1\r\n'
                b'Host: 0.0.0.0:8000\r\n'
                b'Accept: */*\r\n\r\n')

        server = self.make_server()
        req = Request()
        split = Server.splitkeepsep(line, b'\r\n')

        for s in split:
            if req.dynamic_fill(s):
                res = server.handle_req(req)

                self.assertEqual(res.status, 200)
                self.assertEqual(res.reason, 'OK')
                headers_dict = dict(res.headers)
                self.assertTrue(headers_dict.get('Content-Type'))
                self.assertTrue(headers_dict.get('Content-Length'))

    def test_server_context_manager(self):
        s = self.make_server()
        try:
            with s:
                pass
        except AttributeError:
            self.fail()

    def send_req_and_shutdown(self, server):
        req = b'GET / HTTP/1.1\r\nHost: 0.0.0.0\r\nAccept: */*\r\n\r\n'
        with open(CONFIG_PATH) as cfg:
            data = json.load(cfg)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((data['host'], data['port']))
            s.sendall(req)
        except Exception as e:
            pass
        data = []
        while True:
            line = s.recv(Server.MAX_LINE)
            print(line)
            if line in [b'', b'\n']:
                break
            data.append(line)
        server.shutdown()
        s.close()

        res = b''.join(data).decode()
        self.assertTrue(res)

    def test_serving(self):
        server = self.make_server()
        request_task = multiprocessing.Process(
            target=self.send_req_and_shutdown,
            args=(server,))

        with server as s:
            request_task.start()
            try:
                with AsyncStopper(1):
                    s.serve()
            except StopIteration:
                pass
        request_task.terminate()

    class MockWrite:
        def __init__(self):
            self.out_buff = {0: [b'buff']}

    class MockClient:
        def __init__(self):
            self.fileno = lambda: 0
            self.recvd = b''

        def sendall(self, data):
            self.recvd += data

    def test_write(self):
        w, c = ServerTests.MockWrite(), ServerTests.MockClient()
        Server._write(w, c)
        self.assertEqual(c.recvd, b'buff')


if __name__ == '__main__':
    unittest.main()
