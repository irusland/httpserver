from pymongo import MongoClient
from secret_tokens.mongo_secret import LOGIN, PASSWORD, DB_NAME


CONNECT_STRING = (f'mongodb+srv://{LOGIN}:{PASSWORD}'
                  f'@cluster0.zbaqj.mongodb.net/{DB_NAME}'
                  f'?retryWrites=true&w=majority')


def connect():
    return MongoClient(CONNECT_STRING)


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


def insert_document(collection, data):
    """ Function to insert a document into a collection and
    return the document's id.
    """
    return collection.insert_one(data).inserted_id


if __name__ == '__main__':
    main()
