import json
import unittest
import threading
import multiprocessing
import os

from httpserver import Server


class MyTestCase(unittest.TestCase):
    def server_run(self):
        with open('config.json') as cfg:
            data = json.load(cfg)
        server = Server(data['host'], data['port'], data['server'], log=False)
        with server as s:
            s.serve()

    def test_add_text(self):
        server = multiprocessing.Process(target=self.server_run)
        server.start()

        with open('get.txt') as cmdfile:
            cmd = cmdfile.read()
            with os.popen(cmd) as outfile:
                out = outfile.read()
                with open('get_empty_res.txt') as resfile:
                    res = resfile.read()
                    self.assertEqual(out, res)

        server.terminate()


if __name__ == '__main__':
    unittest.main()
