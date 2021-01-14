class User:
    def __init__(self, email, name):
        self.name = name
        self.email = email

    def dump(self):
        return self.__dict__

    @staticmethod
    def from_dict(d):
        return User(d['email'], d['name'])