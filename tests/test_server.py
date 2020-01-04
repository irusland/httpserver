import io
import json
import multiprocessing
import os
import socket
import tempfile
import time
import unittest
import random

from backend.configurator import Configurator
from backend.response import Response
from backend.router.router import Router
from defenitions import CONFIG_PATH, ROOT_DIR
from backend.logger import LogLevel
from backend.request import Request
from backend.stopper import AsyncStopper
from httpserver import Server
from tests.test_router import PathFinderTests


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tf = tempfile.NamedTemporaryFile(mode='w', delete=True)
        self.cfg_path = self.tf.name
        with open(self.cfg_path, "w") as f:
            f.write(ServerTests.CONFIG)

        self.configurator = Configurator.init(self.cfg_path)
        self.rules = self.configurator.get('rules')

    def boot_server(self):
        server = self.make_server()
        with server as s:
            print('booted')
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
        split = Request.split_keep_sep(line, b'\r\n')

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

    def test_send_req_and_shutdown(self):
        request_task = multiprocessing.Process(target=self.boot_server)
        request_task.start()
        time.sleep(1)

        req = b'GET / HTTP/1.1\r\nHost: 0.0.0.0\r\nAccept: */*\r\n' \
              b'Connection: keepalive\r\n\r\n'
        with open(self.cfg_path) as cfg:
            data = json.load(cfg)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((data['host'], data['port']))
        data = []

        # Check page caching
        for _ in range(2):
            try:
                s.sendall(req)
            except Exception as e:
                print(e)
                pass
            try:
                while True:
                    line = s.recv(Server.MAX_LINE)
                    if line in [b'', b'\n']:
                        break
                    data.append(line)
            except socket.error:
                pass

        request_task.terminate()
        s.close()

        res = b''.join(data).decode()
        self.assertTrue(res)

    def test_close(self):
        server = self.make_server()
        with server as s:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            with open(CONFIG_PATH) as cfg:
                data = json.load(cfg)
            try:
                conn.connect((data['host'], data['port']))
            except Exception:
                pass
            s.close(conn)

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

    def test_get_picture(self):
        req_line = b'GET /c.png HTTP/1.1\r\n' \
                   b'Host: 0.0.0.0\r\n' \
                   b'Accept: */*\r\n\r\n'
        server = self.make_server()
        req = Request.fill_from_line(req_line)
        res: Response = server.handle_req(req)
        with open(os.path.join(ROOT_DIR, 'tmp', 'c.png'), 'rb') as pic:
            self.assertEqual(res.body, pic.read())

    def test_show_files(self):
        req_line = b'GET /show_files HTTP/1.1\r\n' \
                   b'Host: 0.0.0.0\r\n' \
                   b'Accept: */*\r\n\r\n'
        server = self.make_server()
        req = Request.fill_from_line(req_line)

        res: Response = server.handle_req(req)
        js = json.loads(res.body)
        dlist = os.listdir(os.path.join(ROOT_DIR, "tmp", "saved"))
        self.assertListEqual(js, dlist)

    def test_upload(self):
        fname = 'testu.txt'
        internals = b'test> text'
        req_line = (
            b'POST /save HTTP/1.1\r\n'
            b'Host: 0.0.0.0:8000\r\n'
            b'Content-Type: multipart/form-data; '
            b'boundary=----WebKitFormBoundary5xldizqf1DVBvoUw\r\n'
            b'Accept-Encoding: gzip, deflate\r\n'
            b'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,'
            b'*/*;q=0.8\r\n'
            b'Content-Length: 193\r\n'
            b'\r\n'
            b'------WebKitFormBoundary5xldizqf1DVBvoUw\r\n'
            b'Content-Disposition: form-data; name="file"; '
            b'filename="testu.txt"\r\n'
            b'Content-Type: text/plain\r\n'
            b'\r\n'
            b'test> text\r\n'
            b'------WebKitFormBoundary5xldizqf1DVBvoUw--\r\n')
        server = self.make_server()
        req = Request.fill_from_line(req_line)

        res: Response = server.handle_req(req)

        self.assertEqual(res.status, 301)
        self.assertEqual(res.reason, 'Moved Permanently')

        fpath = os.path.join(ROOT_DIR, 'tmp', 'saved', fname)
        if os.path.exists(fpath):
            with open(fpath, 'rb') as f:
                t = f.read()
                self.assertEqual(t, internals)
            os.remove(fpath)
        else:
            self.fail()

    def guest_book_get(self, server):
        req_line = (
            b'GET /posts HTTP/1.1\r\n'
            b'Host: 0.0.0.0:8000\r\n'
            b'Accept: */*\r\n'
            b'Accept-Language: en-us\r\n'
            b'Accept-Encoding: gzip, deflate\r\n'
            b'\r\n')

        req = Request.fill_from_line(req_line)
        return server.handle_req(req)

    def test_guest_book_get(self):
        server = self.make_server()
        res: Response = self.guest_book_get(server)

        self.assertEqual(json.loads(res.body),
                         [{"username": "Ruslan", "post": "Post"}])

    def test_guest_book_post(self):
        req_line = (
            b'POST /post HTTP/1.1\r\n'
            b'Host: 0.0.0.0:8000\r\n'
            b'Content-Type: application/x-www-form-urlencoded\r\n'
            b'Accept-Encoding: gzip, deflate\r\n'
            b'Upgrade-Insecure-Requests: 1\r\n'
            b'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,'
            b'*/*;q=0.8\r\n'
            b'Content-Length: 17\r\n'
            b'Accept-Language: en-us\r\n'
            b'\r\n'
            b'username=a&post=b')
        server = self.make_server()
        req = Request.fill_from_line(req_line)
        res: Response = server.handle_req(req)

        self.assertEqual(res.body,
                         b"POST ADDED {'username': ['a'], 'post': ['b']}")

        res = self.guest_book_get(server)

        self.assertEqual(json.loads(res.body),
                         [{"username": "Ruslan", "post": "Post"},
                          {'post': ['b'], 'username': ['a']}])

    CONFIG = ('{"host":"0.0.0.0","port":8000,"rules":{"/":"tmp/index.html",'
              '"/upload":"tmp/upload.html","/save":{"handler":{'
              '"source":"handlers/upload.py","post":"save"}},"/show_files":{'
              '"handler":{"source":"handlers/upload.py","get":"show"}},'
              '"/my_guest_book":"tmp/my_guest_book.html","/posts":{'
              '"handler":{"source":"handlers/my_guest_book.py",'
              '"get":"get_posts"}},"/post":{"handler":{'
              '"source":"handlers/my_guest_book.py","post":"handle_post"}},'
              '"/c.png":{"path":"tmp/c.png","headers":[["Content-Type",'
              '"text/html"],["Content-Disposition","inline; '
              'filename=custom.png"]]},'
              '"/favicon.ico":"tmp/pictures/favicon.ico",'
              '"/index.html":"tmp/index.html","/2.html":"tmp/pages/2.html",'
              '"/1.2.3.txt":"tmp/1.2.3.txt","/page-load-errors['
              'extras].css":{"path":"pages/page-load-errors[extras].css",'
              '"mime":"text/css"},"/[name].html":"tmp/pages/[name].html",'
              '"/[name].css":"tmp/pages/css/[name].css","/[name].['
              'ext]":"tmp/pictures/[name].[ext]","/png/['
              'name].png":"tmp/pictures/[name].png","/pictures/['
              'ext]/1":"tmp/pictures/1.[ext]","/[day]-[n]/[month]/['
              'year]":"tmp/dates/[year]/[month]/[day]/[n].png","/[DD]/[MM]/['
              'YY]":"tmp/dates/[DD].[MM].[YY].png","/mime/":{'
              '"path":"tmp/pictures/1.png","mime":"text/txt"},"/big":{'
              '"path":"tmp/pictures/chroma.jpg","mime":"image/jpg"},'
              '"/[file].[ext]":"tmp/[file].[ext]"},"error-pages":{'
              '"PAGE_NOT_FOUND":"pages/PAGE_NOT_FOUND.html"}}')


if __name__ == '__main__':
    unittest.main()
