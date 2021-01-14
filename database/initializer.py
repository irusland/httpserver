import uuid

from objects.restaurant import Restaurant
import database

RESTAURANTS = [
    Restaurant(uuid.uuid4().hex,
               '65 Broadway',
               'Restaurant description ...',
               ('00:00', '23:00'),
               ['https://www.hot-dinners.com/images/stories/blog/2019/pictureteam.jpg',
                'Alain-Ducasse-scaled.jpg']),
    Restaurant(uuid.uuid4().hex,
               '730 Park Avenue',
               'Restaurant description ...',
               ('11:00', '23:00'),
               ['https://www.irishtimes.com/image-creator/?id=1.3898155&origw=1440']),
    Restaurant(uuid.uuid4().hex,
               '52 Broadway',
               '<h1>no  restaurant description without picture ...</h1>',
               ('11:00', '23:00'),),
    Restaurant(uuid.uuid4().hex,
               '84th Street station',
               'Restaurant description ...',
               ('10:00', '18:00'),
               available=False),
]


def main():
    manager = database.Database()
    for restaurant in RESTAURANTS:
        manager.add_restaurant(restaurant.dump_all())


if __name__ == '__main__':
    main()
