from copy import deepcopy
from datetime import datetime, timedelta
from typing import Type
# from zoneinfo import ZoneInfo
# import uuid
# from devtools import debug
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection
# from api_server.models.db import TimeRangeModel
from api_server.sessions_store.session import Session
from api_server.sessions_store.terminal_time_range import TerminalTimeRange  #, TestModel, TimeRangeModel
# from api_server.sessions_store.session import Session
from api_server.sessions_store.time_range import TimeRange
from api_server.sessions_store.time_range_store import TimeRangesStore


class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class MongoStore(TimeRangesStore, metaclass=Singleton):
    def __init__(self, host: str, username: str, password: str, collection_type: Type[TimeRange]) -> None:
        super().__init__()
        try:
            client: MongoClient = MongoClient(host=host, port=27017, username=username, uuidRepresentation='standard',
                                              password=password, authMechanism='DEFAULT',
                                              serverSelectionTimeoutMS=2000, tz_aware=True)
            db: Database = client['TimeRanges']
            print("Connected to MongoDB")
            self.collection_type: Type[TimeRange] = collection_type
            self.db_origin_ranges: Collection = db['origin_ranges']
            self.db_prev_merge: Collection = db['prev_merge']
            self.db_schedule: Collection = db['schedule']

            self.db_origin_ranges.create_index([( "finish", ASCENDING )], expireAfterSeconds=10)
            self.db_prev_merge.create_index([( "finish", ASCENDING )], expireAfterSeconds=10)
            self.db_schedule.create_index([( "finish", ASCENDING )], expireAfterSeconds=10)
            self.db_origin_ranges.create_index([( "start", ASCENDING )])
            self.db_prev_merge.create_index([( "start", ASCENDING )])
            self.db_schedule.create_index([( "start", ASCENDING )])
        except TimeoutError as e:
            print(f'Database connection failed: {e}')

        self._init_store()

    def _init_store(self) -> None:
        """
        Возможно тут стоит полностью очищать коллекции prev_merge & schedule, делать merge и
        записывать результат в БД
        """
        # var = list(self.db_origin_ranges.find())
        self.origin_ranges = []
        self.prev_merge = []
        self.schedule = []

        for el in list(self.db_origin_ranges.find()):
            val = self.collection_type(**el)
            self.origin_ranges.append(val)
        for el in list(self.db_prev_merge.find()):
            val = self.collection_type(**el)
            self.prev_merge.append(val)
        for el in list(self.db_schedule.find()):
            val = self.collection_type(**el)
            self.schedule.append(val)
        # self.origin_ranges = [self.collection_type(**el) for el in list(self.db_origin_ranges.find())]
        # self.prev_merge = [self.collection_type(**el) for el in list(self.db_prev_merge.find())]
        # self.schedule = [self.collection_type(**el) for el in list(self.db_schedule.find())]

    def get_schedule(self) -> list[dict]:
        return list(self.db_schedule.find({}, {'_id': False}))

    def append(self, *time_ranges: TimeRange) -> None:
        self._init_store()
        super().append(*time_ranges)

        # _ = [self.db_origin_ranges.replace_one({'_id': tr.get_id()}, tr.dict(), upsert=True) for tr in time_ranges]
        self.db_origin_ranges.delete_many({})
        self.db_origin_ranges.insert_many([deepcopy(tr.dict()) for tr in self.origin_ranges])
        self.db_prev_merge.delete_many({})
        self.db_prev_merge.insert_many([tr.dict() for tr in self.prev_merge])
        self.db_schedule.delete_many({})
        self.db_schedule.insert_many([tr.dict() for tr in self.schedule])

    def remove(self, *element: TimeRange) -> None:
        self._init_store()
        super().remove(*element)
        self.db_origin_ranges.delete_many({})
        self.db_origin_ranges.insert_many([tr.dict() for tr in self.origin_ranges])
        self.db_prev_merge.delete_many({})
        self.db_prev_merge.insert_many([tr.dict() for tr in self.prev_merge])
        self.db_schedule.delete_many({})
        self.db_schedule.insert_many([tr.dict() for tr in self.schedule])

# def to_model(tr: TimeRange) -> TimeRangeModel:
#     model = TimeRangeModel(**tr.dict())
#     return model

# def from_model(tr: dict) -> TimeRange:
#     tr['time_range_id'] = tr.pop('_id')
#     return TimeRange(**tr)

if __name__ == '__main__':
    controller: MongoStore = MongoStore('10.6.1.74', 'root', 'rootpassword', Session)
    # start_time: datetime = datetime.utcnow() + timedelta(seconds=60)
    start_time: datetime = datetime.now().astimezone() + timedelta(seconds=60)
    # start_time: datetime = datetime(2011, 12, 1, 1, 1, 1)
    t_1: TerminalTimeRange = TerminalTimeRange(start_time + timedelta(seconds=5), duration_sec=20, priority=2)
    t_2: TerminalTimeRange = TerminalTimeRange(start_time + timedelta(seconds=91), duration_sec=10, priority=3)
    s1: Session = Session(username='lolkek', start=start_time, duration_sec=10, priority=1)
    s2: Session = Session(username='gdfg', start=start_time + timedelta(seconds=2),  duration_sec=5, priority=2)
    controller.append(s1, s2)
    print(controller.get_schedule())
    # controller.remove(t_2)
    # controller.append(t_1, t_2)

