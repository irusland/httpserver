import unittest

from ihttpy.requests.methods import Method
from ihttpy.requests.response import Response
from ihttpy.routing.configurator import FluentConfigurator
from ihttpy.routing.page import Page


class FluentConfiguratorTestCase(unittest.TestCase):
    def setUp(self):
        self.sut = FluentConfigurator()

    def tearDown(self):
        pass

    def test_wraps_inline(self):
        wrap = self.sut.on(Method.GET).at('/')

        def func(req, srv):
            return Response('OK', 200)
        func = wrap(func)

        res: Response = func(None, None)

        self.assertIsInstance(res, Response)

    def test_wraps_as_decorator(self):
        @self.sut.on(Method.GET).at('/')
        def func(req, srv):
            return Response('OK', 200)

        res: Response = func(None, None)

        self.assertIsInstance(res, Response)

    def test_configurator_rules_are_pages(self):
        @self.sut.on(Method.GET).at('/')
        def func(req, srv):
            return Response('OK', 200)
        rules = self.sut._get_rules()

        page = rules.get('/')

        self.assertIsInstance(page, Page)

    def test_double_wrap_func_address_does_not_change(self):
        @self.sut.on(Method.GET).at('/1')
        @self.sut.on(Method.POST).at('/2')
        def func(req, srv):
            return Response('OK', 200)
        rules = self.sut._get_rules()
        page1: Page = rules.get('/1')
        page2: Page = rules.get('/2')

        f1 = page1.get_handler(Method.GET)
        f2 = page2.get_handler(Method.POST)

        self.assertEqual(f1, f2)

    def test_2_decorators_on_same_route_combines(self):
        @self.sut.on(Method.GET).at('/')
        @self.sut.on(Method.POST).at('/')
        def func(req, srv):
            return Response('OK', 200)
        rules = self.sut._get_rules()
        page: Page = rules.get('/')

        f1 = page.get_handler(Method.GET)
        f2 = page.get_handler(Method.POST)

        self.assertEqual(f1, f2)

    def test_2_decorators_2_func_on_same_route_combines(self):
        @self.sut.on(Method.GET).at('/')
        def func1(req, srv):
            return Response('OK', 200)

        @self.sut.on(Method.OPTIONS).at('/')
        def func2(req, srv):
            return Response('OK', 200)
        rules = self.sut._get_rules()
        page: Page = rules.get('/')
        print(rules, page, sep='\n')

        f1 = page.get_handler(Method.GET)
        f2 = page.get_handler(Method.OPTIONS)

        self.assertEqual(f1, func1)
        self.assertEqual(f2, func2)
        self.assertNotEqual(f1, f2)

    def test_1_decorator_logic_or(self):
        @self.sut.on(Method.GET | Method.POST).at('/')
        def func(req, srv):
            return Response('OK', 200)
        rules = self.sut._get_rules()
        page: Page = rules.get('/')

        f1 = page.get_handler(Method.GET)
        f2 = page.get_handler(Method.POST)

        self.assertEqual(f1, f2)

    def test_method_is_not_in_rules(self):
        @self.sut.on(Method.GET).at('/')
        def func(req, srv):
            return Response('OK', 200)

        rules = self.sut._get_rules()
        page: Page = rules.get('/')

        f = page.get_handler(Method.POST)

        self.assertIsNone(f)

    def _add_rule(self, method: Method, route: str):
        @self.sut.on(method).at(route)
        def func(req, srv):
            return Response('OK', 200)

        self.rules = self.sut._get_rules()

    def test_adds_rule(self):
        @self.sut.on(Method.GET).at('/')
        def func(req, srv):
            return Response('OK', 200)
        self.rules = self.sut._get_rules()

        page = self.rules.get('/')

        self.assertIsInstance(page, Page)
        self.assertEqual(page.get_function_name_for_method(
            Method.GET.to_simple_str()), 'func')


if __name__ == '__main__':
    unittest.main()
