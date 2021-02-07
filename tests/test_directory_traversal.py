import unittest

from ihttpy.exceptions import errors
from ihttpy.requests import sender
from ihttpy.requests.methods import Method
from ihttpy.requests.request import Request
from ihttpy.routing.configurator import FluentConfigurator
from ihttpy.routing.router import Router


class DirectoryTraversalTests(unittest.TestCase):
    def test_does_not_match_when_has_dots_in_url(self):
        config = FluentConfigurator()
        router = Router()

        @config.on(Method.GET).at('/[file].[ext]')
        def func(req: Request, srv):
            self.fail('Exploited')

        exploits = [
            '/pictures/%2E%2E/%2E%2E/secret_tokens/mongo_secret.py',
            '/pictures%2F%252E%252E%2F%252E%252E%2Fsecret_tokens%2Fmongo_secret.py'
        ]

        rules = config._get_rules()

        for exploit in exploits:
            self.assertRaises(errors.Error,
                              router.find_page_description,
                              *(exploit, rules))


if __name__ == '__main__':
    unittest.main()
