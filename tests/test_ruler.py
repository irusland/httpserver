import os
import unittest

from defenitions import ROOT_DIR
from ruler import Ruler


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.ruler = Ruler()
        self.rules = self.ruler.get_rules()

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

    def test_file_exists_no_rule(self):
        self.assertFileNotFound('/norulefile.py')

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


if __name__ == '__main__':
    unittest.main()
