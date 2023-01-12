from __future__ import annotations
from datetime import datetime, timedelta
import os
from typing import Type

from bson import CodecOptions, UuidRepresentation
# from zoneinfo import ZoneInfo
# import uuid
# from devtools import debug
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from pytz import utc
from api_server.sessions_manager.session import Session
from api_server.sessions_manager.time_range import TimeRange
from api_server.sessions_manager.time_range_store import TimeRangesStore


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
            db: Database = client.get_database('TimeRanges')
            print("Connected to MongoDB")
            self.collection_type: Type[TimeRange] = collection_type
            codec_options = CodecOptions(tz_aware=True, uuid_representation=UuidRepresentation.STANDARD)
            self.db_origin_ranges: Collection = db.get_collection('origin_ranges', codec_options=codec_options)
            self.db_prev_merge: Collection = db.get_collection('prev_merge', codec_options=codec_options)
            self.db_schedule: Collection = db.get_collection('schedule', codec_options=codec_options)
            self.db_missed_sessions: Collection = db.get_collection('missed', codec_options=codec_options)

            self.db_origin_ranges.create_index([( "finish", ASCENDING )], expireAfterSeconds=10)
            self.db_prev_merge.create_index([( "finish", ASCENDING )], expireAfterSeconds=10)
            self.db_schedule.create_index([( "finish", ASCENDING )], expireAfterSeconds=10)
            self.db_origin_ranges.create_index([( "start", ASCENDING )])
            self.db_prev_merge.create_index([( "start", ASCENDING )])
            self.db_schedule.create_index([( "start", ASCENDING )])
        except TimeoutError as e:
            print(f'Database connection failed: {e}')

        self._init_store()

    def __init_collection(self, local: list, db: Collection) -> None:
        local = []
        for el in list(db.find()):
            val: TimeRange = self.collection_type(**el)
            local.append(val)

    def _init_store(self) -> None:
        self.__init_collection(self.origin_ranges, self.db_origin_ranges)
        self.__init_collection(self.prev_merge, self.db_prev_merge)
        self.__init_collection(self.schedule, self.db_schedule)

    def get_schedule(self) -> list[dict]:
        return list(self.db_schedule.find({}, {'_id': False}))  # , sort=[('next_run_time', ASCENDING)]

    def update_all(self) -> None:
        self.db_origin_ranges.delete_many({})
        self.db_prev_merge.delete_many({})
        self.db_schedule.delete_many({})

        self.schedule = [tr for tr in self.schedule if tr.start < datetime.now.astimezone(utc)]

        if len(self.origin_ranges) > 0:
            self.db_origin_ranges.insert_many([tr.dict() for tr in self.origin_ranges])
        if len(self.prev_merge) > 0:
            self.db_prev_merge.insert_many([tr.dict() for tr in self.prev_merge])
        if len(self.schedule) > 0:
            self.db_schedule.insert_many([tr.dict() for tr in self.schedule])

    def append(self, *time_ranges: TimeRange) -> None:
        super().append(*time_ranges)
        self.update_all()

    def remove(self, *element: TimeRange) -> None:
        super().remove(*element)
        self.update_all()

    def simple_remove(self, *element: TimeRange) -> None:
        super().simple_remove(*element)
        self.update_all()


    def add_missed(self, *time_ranges: TimeRange) -> None:
        self.db_missed_sessions.insert_many([tr.dict() for tr in time_ranges])


if __name__ == '__main__':
    mongo_username = os.environ.get('MONGO_DB_USERNAME', 'root')
    mongo_pass = os.environ.get('MONGO_DB_PASSWORD', 'rootpassword')
    controller: MongoStore = MongoStore(os.environ.get('GS_ADDR', '10.13.13.6'), mongo_username, mongo_pass, Session)
    # start_time: datetime = datetime.utcnow() + timedelta(seconds=60)
    start_time: datetime = datetime.now().astimezone() + timedelta(seconds=60)
    # start_time: datetime = datetime(2011, 12, 1, 1, 1, 1)
    # t_1: TerminalTimeRange = TerminalTimeRange(start_time + timedelta(seconds=5), duration_sec=20, priority=2)
    # t_2: TerminalTimeRange = TerminalTimeRange(start_time + timedelta(seconds=91), duration_sec=10, priority=3)
    s1: Session = Session(username='lolkek', start=start_time, duration_sec=10, priority=1)
    s2: Session = Session(username='gdfg', start=start_time + timedelta(seconds=2),  duration_sec=5, priority=2)
    controller.append(s1, s2)
    print(controller.get_schedule())
    # controller.remove(t_2)
    # controller.append(t_1, t_2)
