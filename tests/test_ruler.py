import unittest
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
            '/Users/irusland/Desktop/UrFU/'
            'python/httpserver/tmp/index.html')

    def test_path_for_file_by_rule(self):
        self.assertDestinationsEqual(
            '/2.html',
            '/Users/irusland/Desktop/UrFU/'
            'python/httpserver/tmp/pages/2.html')

    def test_path_for_file_by_any_rule(self):
        self.assertDestinationsEqual(
            '/any.html',
            '/Users/irusland/Desktop/UrFU/'
            'python/httpserver/tmp/pages/any.html')

    def test_path_for_file_in_dir(self):
        self.assertDestinationsEqual(
            '/123.css',
            '/Users/irusland/Desktop/UrFU/'
            'python/httpserver/tmp/pages/css/123.css')

    def test_file_not_found_with_rule(self):
        self.assertFileNotFound('/no.css')

    def test_file_exists_no_rule(self):
        self.assertFileNotFound('/norulefile.py')

    def test_no_file_no_rule(self):
        self.assertFileNotFound('/foo.bar')

    def test_name_with_dots(self):
        self.assertDestinationsEqual(
            '/1.2.3.txt',
            '/Users/irusland/Desktop/UrFU/'
            'python/httpserver/tmp/1.2.3.txt')

    def test_rule_with_slash(self):
        self.assertDestinationsEqual(
            '/',
            '/Users/irusland/Desktop/UrFU/'
            'python/httpserver/tmp/index.html')

    def test_file_in_folder_request(self):
        self.assertDestinationsEqual(
            '/png/1.png',
            '/Users/irusland/Desktop/UrFU/'
            'python/httpserver/tmp/pictures/1.png')


if __name__ == '__main__':
    unittest.main()
