import ctypes
import io
import json
import multiprocessing
import socket
import threading
import time
import unittest

from httpserver import Server
from defenitions import CONFIG_PATH


class MyTestCase(unittest.TestCase):
    def boot_server(self):
        server = self.make_server()
        with server as s:
            s.serve()

    def make_server(self):
        with open(CONFIG_PATH) as cfg:
            data = json.load(cfg)
        return Server(data['host'], data['port'], data['server'],
                      debug=False, accept_refresh=0.1)

    def process_req(self, req):
        with self.make_server() as server:
            file = io.BytesIO(req.encode('utf-8'))
            return server.parse_req_file(file)

    def req_to_str(self, method, target, ver, headers):
        return '\n'.join((
            ' '.join((method, target, ver)),
            '\n'.join(f'{k}: {v}' for k, v in headers.items())))

    def assert_req_parsed(self, m, t, v, h):
        req = self.req_to_str(m, t, v, h)
        p = self.process_req(req)
        method, target, ver, headers = p
        self.assertTupleEqual((m, t, v), (method, target, ver))
        for k in h.keys():
            self.assertEqual(headers.get(k), h.get(k))

    def test_req_parsing(self):
        self.assert_req_parsed('GET', '/2.html', 'HTTP/1.1',
                               {'Host': '0.0.0.0:8000',
                                'Accept': 'text/html'})

    def test_get_res(self):
        str_req = 'GET / HTTP/1.1\n' \
              'Host: 0.0.0.0:8000\n' \
              'Accept: */*\n\n'

        server = self.make_server()
        file = io.BytesIO(str_req.encode('utf-8'))
        parsed_req = server.parse_req_file(file)
        req = server.parsed_req_to_request(*parsed_req, file)
        res = server.handle_req(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.reason, 'OK')
        headers_dict = dict(res.headers)
        self.assertTrue(headers_dict.get('Content-Type'))
        self.assertTrue(headers_dict.get('Content-Length'))

    def test_server_context_manager(self):
        s = self.make_server()
        self.assertTrue(hasattr(s, '__enter__'))
        self.assertTrue(hasattr(s, '__exit__'))
        try:
            with s as server:
                pass
        except Exception as e:
            self.fail()

    def send_req_and_shutdown(self, server):
        time.sleep(2)
        req = b'GET / HTTP/1.1\nHost: 0.0.0.0\n\n'
        with open(CONFIG_PATH) as cfg:
            data = json.load(cfg)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((data['host'], data['port']))
            s.sendall(req)
            print('sent', req)
        except Exception as e:
            print('Cant connect and send', e)
        # finally:
            # s.close()
        data = []
        while True:
            line = s.recv(Server.MAX_LINE)
            if line in [b'', b'\n']:
                break
            data.append(line)
        server.shutdown()
        # for k, v in  threading._active.items():
        #     if '_MainThread' in repr(v):
        #         target_tid = k
        #         print(f'found {k, v}')
        # ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        #     target_tid, ctypes.py_object(StopIteration))
        # if ret == 0:
        #     raise ValueError("Invalid thread ID")
        # elif ret > 1:
        #     ctypes.pythonapi.PyThreadState_SetAsyncExc(target_tid, None)
        #     raise SystemError("PyThreadState_SetAsyncExc failed")
        # print("Successfully set asynchronized exception for", target_tid)

        # print('shutdown')

        s.close()
        # print('closed')
        res = b''.join(data).decode()
        print(res)
        exit(0)


    def test_serving(self):
        server = self.make_server()
        request_task = multiprocessing.Process(
            target=self.send_req_and_shutdown,
            args=(server, ))
        with server as s:
            request_task.start()
            s.serve()
        request_task.terminate()


if __name__ == '__main__':
    unittest.main()
