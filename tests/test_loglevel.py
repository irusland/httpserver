import unittest

from ihttpy.exceptions.logger import LogLevel


class TestLogLevel(unittest.TestCase):
    def test_log_level(self):
        for name in ['console', 'logging']:
            a = LogLevel.from_string(name)
            self.assertEqual(str(a), name)

    def test_value_error(self):
        for name in ['not', 'presented']:
            self.assertRaises(ValueError, LogLevel.from_string, name)


if __name__ == '__main__':
    unittest.main()
