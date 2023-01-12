from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection

class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class MongoStore(metaclass=Singleton):
    def __init__(self, host: str, username: str, password: str) -> None:
        super().__init__()
        try:
            client: MongoClient = MongoClient(host=host, port=27017, username=username, uuidRepresentation='standard',
                                              password=password, authMechanism='DEFAULT',
                                              serverSelectionTimeoutMS=2000, tz_aware=True)
            db: Database = client.get_database('Satellites')
            self.tle_collection: Collection = db.get_collection('tle_collection')
            print("Connected to MongoDB")
        except TimeoutError as e:
            print(f'Database connection failed: {e}')

    def get_tle(self, sat_name: str):
        pass