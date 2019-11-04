import unittest
from ruler import Ruler


class MyTestCase(unittest.TestCase):
    def test_get_abs_path_for_file(self):
        ruler = Ruler()
        r = ruler.get_rules()
        d = ruler.get_destination('/index.html', r, abs=True)
        self.assertEqual('/Users/irusland/Desktop/UrFU/'
                         'python/httpserver/tmp/index.html', d)

    def test_path_for_file_by_rule(self):
        ruler = Ruler()
        r = ruler.get_rules()
        d = ruler.get_destination('/2.html', r, abs=True)
        self.assertEqual('/Users/irusland/Desktop/UrFU/'
                         'python/httpserver/tmp/pages/2.html', d)

    def test_path_for_file_by_any_rule(self):
        ruler = Ruler()
        r = ruler.get_rules()
        d = ruler.get_destination('/any.html', r, abs=True)
        self.assertEqual('/Users/irusland/Desktop/UrFU/'
                         'python/httpserver/tmp/pages/any.html', d)

    def test_path_for_file_in_dir(self):
        ruler = Ruler()
        r = ruler.get_rules()
        d = ruler.get_destination('/123.css', r, abs=True)
        self.assertEqual('/Users/irusland/Desktop/UrFU/'
                         'python/httpserver/tmp/pages/css/123.css', d)


if __name__ == '__main__':
    unittest.main()
