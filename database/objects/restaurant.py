

class Restaurant:
    def __init__(self,
                 id,
                 address,
                 description,
                 working_hours,
                 pictures=None,
                 available=True):
        self.working_hours = working_hours
        # todo hide mongo's '_id': ObjectId('...
        self._id = id
        self.id = id
        self.address = address
        self.description = description
        self.pictures = []
        if pictures:
            self.pictures = pictures
        self.available = available

    SHORT = ['_id', 'id', 'address', 'available']

    def dump(self):
        return {key: self.__dict__[key] for key in self.SHORT}

    def dump_all(self):
        d = self.dump()
        d['description'] = self.description
        d['pictures'] = self.pictures
        d['working_hours'] = self.working_hours
        return d
