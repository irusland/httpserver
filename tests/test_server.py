import json
import multiprocessing
import os
import subprocess
import time
import unittest


from httpserver import Server
from defenitions import CONFIG_PATH, QUERIES_DIR


class MyTestCase(unittest.TestCase):
    def boot_server(self):
        with open(CONFIG_PATH) as cfg:
            data = json.load(cfg)
        server = Server(data['host'], data['port'], data['server'], debug=False)
        with server as s:
            s.serve()

    def get_res(self, cmd_path, res_path):
        server = multiprocessing.Process(target=self.boot_server)
        server.start()

        # wait for server to boot
        time.sleep(1)

        with open(cmd_path) as cmdfile:
            print('debug', cmd_path)
            cmd = cmdfile.read()
            print('debug', cmd)
            with os.popen(cmd) as outfile:
                out = outfile.read()
                print('debug', out)
                server.terminate()
                with open(res_path) as resfile:
                    res = resfile.read()
                    print('debug', res)
                    self.assertMultiLineEqual(out, res)

    def test_get_page(self):
        self.get_res(os.path.join(QUERIES_DIR, 'get_index.txt'),
                     os.path.join(QUERIES_DIR, 'get_index_res.txt'))

    def test_get_by_rule(self):
        self.get_res(os.path.join(QUERIES_DIR, 'get_by_rule.txt'),
                     os.path.join(QUERIES_DIR, 'get_by_rule_res.txt'))


if __name__ == '__main__':
    unittest.main()
