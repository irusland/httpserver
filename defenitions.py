import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')
TESTS_DIR = os.path.join(ROOT_DIR, 'tests')
LOGGER_PATH = os.path.join(ROOT_DIR, 'server.log')
REQUEST_HANDLERS_DIR = os.path.join(ROOT_DIR, 'backend', 'router', 'handlers')
