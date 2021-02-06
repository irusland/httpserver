import os
import unittest

from ihttpy.routing.page import Page
from defenitions import ROOT_DIR


class PageTest(unittest.TestCase):
    def test_initialisation(self):
        description = {
            "handler": {
                "source": "infrastructure/routing/handlers/my_guest_book.py",
                "get": "get_posts",
                "post": "handle_post",
            },
            "path": "path",
            "mime": "mime",
            "headers": "headers"
        }
        page = Page(description)
        self.assertEqual(page.get_path(), description.get("path"))
        self.assertEqual(page.get_mime(), description.get("mime"))
        self.assertEqual(page.get_abs_handler_path(),
                         os.path.join(ROOT_DIR,
                                      description
                                      .get("handler")
                                      .get("source")))
        self.assertEqual(page.get_function_name_for_method("get"),
                         description.get("handler").get("get"))
        self.assertEqual(page.get_function_name_for_method("post"),
                         description.get("handler").get("post"))


if __name__ == '__main__':
    unittest.main()
