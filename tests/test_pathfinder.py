import os
import unittest
import random

from backend.configurator import Configurator
from defenitions import ROOT_DIR
from backend.router import Router


class PathFinderTests(unittest.TestCase):
    def setUp(self):
        self.cfg_path = os.path.join(ROOT_DIR, 'tests',
                                     f'cfg{random.random()}.tmp')
        with open(self.cfg_path, "w") as f:
            f.write(self.CONFIG)
        self.configurator = Configurator.init(self.cfg_path)
        self.ruler = Router()
        self.rules = self.configurator.get('rules')

    def tearDown(self):
        os.remove(self.cfg_path)

    def assertDestinationsEqual(self, url, path, rules=None):
        if rules is None:
            rules = self.rules
        d = self.ruler.get_destination(url, rules, absolute=True)
        self.assertEqual(path, d)

    def assertFileNotFound(self, url):
        self.assertRaises(
            FileNotFoundError,
            self.ruler.get_destination,
            *(url, self.rules, True))

    def test_get_abs_path_for_file(self):
        self.assertDestinationsEqual(
            '/index.html',
            os.path.join(ROOT_DIR, 'tmp/index.html'))

    def test_path_for_file_by_rule(self):
        self.assertDestinationsEqual(
            '/2.html', os.path.join(ROOT_DIR, 'tmp/pages/2.html'))

    def test_path_for_file_by_any_rule(self):
        self.assertDestinationsEqual(
            '/any.html', os.path.join(ROOT_DIR, 'tmp/pages/any.html'))

    def test_path_for_file_in_dir(self):
        self.assertDestinationsEqual(
            '/123.css', os.path.join(ROOT_DIR, 'tmp/pages/css/123.css'))

    def test_file_not_found_with_rule(self):
        self.assertFileNotFound('/no.css')

    def test_no_file_no_rule(self):
        self.assertFileNotFound('/foo.bar')

    def test_name_with_dots(self):
        self.assertDestinationsEqual(
            '/1.2.3.txt', os.path.join(ROOT_DIR, 'tmp/1.2.3.txt'))

    def test_rule_with_slash(self):
        self.assertDestinationsEqual(
            '/', os.path.join(ROOT_DIR, 'tmp/index.html'))

    def test_file_in_folder_request(self):
        self.assertDestinationsEqual(
            '/pictures/png/1', os.path.join(ROOT_DIR, 'tmp/pictures/1.png'))

    def test_file_with_mime(self):
        url = '/mime/'
        self.assertDestinationsEqual(
            url,
            os.path.join(ROOT_DIR, 'tmp/pictures/1.png'))
        t = self.ruler.get_type(url, self.rules)
        self.assertEqual(t, 'text/txt')

    def test_space_character(self):
        self.assertDestinationsEqual(
            '/new page.html', os.path.join(ROOT_DIR, 'tmp/new page.html'))

    CONFIG = r'{"host": "0.0.0.0","port": 8000,"rules": {"/" : ' \
             r'"tmp/index.html","/favicon.ico" : "tmp/pictures/favicon.ico",' \
             r'"/index.html" : "tmp/index.html","/page-load-errors[' \
             r'extras].css": {"path": "pages/page-load-errors[extras].css",' \
             r'"mime": "text/css"},"/[name].html" : "tmp/pages/[name].html",' \
             r'"/[name].css" : "tmp/pages/css/[name].css","/[name].[ext]" : ' \
             r'"tmp/pictures/[name].[ext]","/png/[name].png" : ' \
             r'"tmp/pictures/[name].png","/pictures/[ext]/1" : ' \
             r'"tmp/pictures/1.[ext]","/[day]-[n]/[month]/[year]" : ' \
             r'"tmp/dates/[year]/[month]/[day]/[n].png","/[DD]/[MM]/[YY]" : ' \
             r'"tmp/dates/[DD].[MM].[YY].png","/mime/" : {"path" : ' \
             r'"tmp/pictures/1.png","mime" : ' \
             r'"text/txt"},"/big" : { "path" : ' \
             r'"tmp/pictures/chroma.jpg", "mime" : "image/jpg" },"/[file].[' \
             r'ext]" : "tmp/[file].[ext]"},"error-pages":' \
             r' {"PAGE_NOT_FOUND": ' \
             r'"pages/PAGE_NOT_FOUND.html"}} '


if __name__ == '__main__':
    unittest.main()
