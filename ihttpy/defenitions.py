import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, '', 'environment.json')
SUPPORTED_METHODS = ['GET', 'POST', 'OPTIONS', 'PUT', 'DELETE']
