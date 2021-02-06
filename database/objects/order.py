import uuid


class Order:
    def __init__(self, user, restaurant, time, comment, is_validated=False,
                 validation_url=None):
        self.id = uuid.uuid4().hex
        # todo disable mongo's ids
        self._id = self.id
        self.is_validated = is_validated

        self.validation_url = f'accept-{uuid.uuid4().hex}{uuid.uuid4().hex}'
        if validation_url:
            self.validation_url = validation_url

        self.comment = comment
        self.time = time
        self.restaurant = restaurant
        self.user = user

    def __str__(self):
        return ', '.join(self.dump())

    def __repr__(self):
        return self.__str__()

    def dump(self):
        d = dict()
        for k, v in self.__dict__.items():
            o = v
            if hasattr(v, 'dump'):
                o = v.dump()
            d[k] = o
        d['_id'] = self._id
        return d

    @staticmethod
    def from_dict(d):
        values = [d[i] for i in ['user', 'restaurant', 'time',
                                 'comment', 'is_validated',
                                 'validation_url']]
        print(values)
        return Order(*values)
