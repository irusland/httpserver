from pymongo import MongoClient
from secret_tokens.mongo_secret import LOGIN, PASSWORD, DB_NAME


CONNECT_STRING = (f'mongodb+srv://{LOGIN}:{PASSWORD}'
                  f'@cluster0.zbaqj.mongodb.net/{DB_NAME}'
                  f'?retryWrites=true&w=majority')


class Database:
    RESTAURANT_TABLE = 'restaurants'
    USER_TABLE = 'users'
    ORDER_TABLE = 'orders'

    def __init__(self):
        self.db = self.connect()

    def connect(self):
        client = MongoClient(CONNECT_STRING)
        return client[DB_NAME]

    def add_restaurant(self, restaurant):
        restaurants = self.db[self.RESTAURANT_TABLE]
        id = self._insert_document(restaurants, restaurant)
        return id

    def get_restaurant(self, id):
        restaurants = self.db[self.RESTAURANT_TABLE]
        found_restaurant = self._find_document(restaurants, {'id': id})
        return found_restaurant

    def get_restaurants(self):
        restaurants = self.db[self.RESTAURANT_TABLE]
        return list(restaurants.find())

    def add_user(self, user):
        users = self.db[self.USER_TABLE]
        id = self._insert_document(users, user)
        return id

    def get_user(self, email):
        users = self.db[self.USER_TABLE]
        found = self._find_document(users, {'email': email})
        return found

    def add_order(self, order):
        orders = self.db[self.ORDER_TABLE]
        id = self._insert_document(orders, order)
        return id

    def get_order(self, search_dict):
        orders = self.db[self.ORDER_TABLE]
        found = self._find_document(orders, search_dict)
        return found

    def update_order(self, query_elements, new_values):
        orders = self.db[self.ORDER_TABLE]
        self._update_document(orders, query_elements, new_values)

    def get_orders(self):
        orders = self.db[self.ORDER_TABLE]
        return list(orders.find())

    def _insert_document(self, collection, data):
        return collection.insert_one(data).inserted_id

    def _find_document(self, collection, elements, multiple=False):
        if multiple:
            results = collection.find(elements)
            return [r for r in results]
        else:
            return collection.find_one(elements)

    def _update_document(self, collection, query_elements, new_values):
        collection.update_one(query_elements, {'$set': new_values})


def main():
    client = connect()
    print('connected')
    print(client.db)

    db = client['SeriesDB']
    series_collection = db['series']

    new_show = {
        "name": "FRIENDS",
        "year": 1994
    }
    print(insert_document(series_collection, new_show))


if __name__ == '__main__':
    main()
