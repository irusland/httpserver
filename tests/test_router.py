import os
import unittest
from tempfile import NamedTemporaryFile

from ihttpy.routing.configurator import Configurator
from tests.defenitions_for_test import TEST_DATA_DIR, get_config
from ihttpy.routing.router import Router


class PathFinderTests(unittest.TestCase):
    def setUp(self):
        self.cfg_file = NamedTemporaryFile(delete=False)
        self.cfg_file.write(get_config().encode())
        self.cfg_file.close()
        self.configurator = Configurator(self.cfg_file.name)
        self.ruler = Router()
        self.rules = self.configurator._get_rules()

    def tearDown(self):
        os.unlink(self.cfg_file.name)

    def assertDestinationsEqual(self, url, path, rules=None):
        if rules is None:
            rules = self.rules
        found_file_path = self.ruler.get_destination(url, rules, absolute=True)
        self.assertEqual(path, found_file_path)

    def assertFileNotFound(self, url):
        self.assertRaises(
            FileNotFoundError,
            self.ruler.get_destination,
            *(url, self.rules, True))

    @staticmethod
    def to_absolute(*relative_path):
        return os.path.join(TEST_DATA_DIR, *relative_path)

    def test_get_abs_path_for_file(self):
        self.assertDestinationsEqual(
            '/index.html',
            self.to_absolute('index.html'))

    def test_path_for_file_by_rule(self):
        self.assertDestinationsEqual(
            '/2.html',
            self.to_absolute('pages', '2.html'))

    def test_path_for_file_by_any_rule(self):
        self.assertDestinationsEqual(
            '/any.html',
            self.to_absolute('pages', 'any.html'))

    def test_path_for_file_in_dir(self):
        self.assertDestinationsEqual(
            '/123.css',
            self.to_absolute('pages', 'css', '123.css'))

    def test_file_not_found_with_rule(self):
        self.assertFileNotFound('/no.css')

    def test_no_file_no_rule(self):
        self.assertFileNotFound('/foo.bar')

    def test_name_with_dots(self):
        self.assertDestinationsEqual(
            '/1.2.3.txt',
            self.to_absolute('1.2.3.txt'))

    def test_rule_with_slash(self):
        self.assertDestinationsEqual(
            '/',
            self.to_absolute('index.html'))

    def test_file_in_folder_request(self):
        self.assertDestinationsEqual(
            '/pictures/png/1',
            self.to_absolute('pictures', '1.png'))

    def test_file_with_mime(self):
        url = '/mime/'
        self.assertDestinationsEqual(
            url,
            self.to_absolute('pictures', '1.png'))
        t = self.ruler.get_type(url, self.rules)
        self.assertEqual('text/txt', t)


if __name__ == '__main__':
    unittest.main()
