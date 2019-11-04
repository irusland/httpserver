import json
import multiprocessing
import os
import unittest


from httpserver import Server
from defenitions import CONFIG_PATH, QUERIES_DIR


class MyTestCase(unittest.TestCase):
    def server_run(self):
        with open(CONFIG_PATH) as cfg:
            data = json.load(cfg)
        server = Server(data['host'], data['port'], data['server'], log=False)
        with server as s:
            s.serve()

    def test_add_text(self):
        server = multiprocessing.Process(target=self.server_run)
        server.start()

        with open(os.path.join(QUERIES_DIR, 'get.txt')) as cmdfile:
            cmd = cmdfile.read()
            with os.popen(cmd) as outfile:
                out = outfile.read()
                server.terminate()
                with open(os.path.join(QUERIES_DIR, 'get_empty_res.txt')) \
                        as resfile:
                    res = resfile.read()
                    self.assertMultiLineEqual(out, res)


if __name__ == '__main__':
    unittest.main()
