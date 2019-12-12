class Page:
    def __init__(self, config_description):
        self.path = None
        self.mime = None
        self.headers = None
        self.handler_path = None
        self.get_func_name = None
        self.post_func_name = None
        if not isinstance(config_description, dict):
            self.path = config_description
        else:
            if 'path' in config_description:
                self.path = config_description.get('path')
            if 'mime' in config_description:
                self.mime = config_description.get('mime')
            if 'headers' in config_description:
                self.headers = config_description.get('headers')
            if 'handler' in config_description:
                handler = config_description.get('handler')
                self.handler_path = handler.get('source')
                self.get_func_name = handler.get('get')
                self.post_func_name = handler.get('post')

    def get_path(self) -> str:
        return self.path

    def get_mime(self) -> str:
        return self.mime

    def get_handler_path(self) -> str:
        return self.handler_path

    def get_get_func_name(self) -> str:
        return self.get_func_name

    def get_post_func_name(self) -> str:
        return self.post_func_name

    def get_headers(self) -> list:
        return self.headers
