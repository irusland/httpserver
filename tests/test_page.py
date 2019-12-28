import unittest

from backend.router.page import Page


class PageTest(unittest.TestCase):
    def test_initialisation(self):
        description = {
            "handler": {
                "source": "backend/router/handlers/my_guest_book.py",
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
        self.assertEqual(page.get_handler_path(), description.get(
            "handler").get("source"))
        self.assertEqual(page.get_get_func_name(), description.get(
            "handler").get("get"))
        self.assertEqual(page.get_post_func_name(), description.get(
            "handler").get("post"))


if __name__ == '__main__':
    unittest.main()
