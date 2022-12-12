from __future__ import annotations
# from datetime import datetime, timedelta
from uuid import UUID
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.results import DeleteResult, InsertOneResult

from api_server.models.db import ResultSessionModel, UserScriptModel

class Singleton(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class UserStore(metaclass=Singleton):
    def __init__(self, host: str, username: str, password: str) -> None:
        super().__init__()
        try:
            client: MongoClient = MongoClient(host=host, port=27017, username=username, uuidRepresentation='standard',
                                              password=password, authMechanism='DEFAULT',
                                              serverSelectionTimeoutMS=2000)
            db: Database = client['UserData']
            print("Connected to MongoDB")
            self.scripts: Collection = db['scripts']
            self.sessions: Collection = db['sessions']
            self.scripts.create_index([( "user_id", ASCENDING )])
        except TimeoutError as e:
            print(f'Database connection failed: {e}')

    def save_session_result(self, model: ResultSessionModel):
        result: InsertOneResult = self.sessions.insert_one(model.dict())
        return result.inserted_id

    def get_session_result_by_id(self, session_id: UUID) -> ResultSessionModel | None:
        result: dict | None = self.sessions.find_one({'_id': session_id})
        if result is not None:
            return ResultSessionModel.parse_obj(result)
        return None

    def get_session_result_by_user(self, user_id: UUID) -> list[ResultSessionModel]:
        return [ResultSessionModel.parse_obj(result) for result in list(self.sessions.find({'_id': user_id}))]

    def save_script(self, script: UserScriptModel):
        result: InsertOneResult = self.scripts.insert_one(script.dict(by_alias=True))
        return result.inserted_id

    def get_script(self, script_id: UUID) -> UserScriptModel | None:
        result: dict | None = self.scripts.find_one({'_id': script_id})
        if result is not None:
            return UserScriptModel.parse_obj(result)
        return None

    def get_users_scripts(self, user_id: UUID) -> list[UserScriptModel]:
        return [UserScriptModel.parse_obj(data) for data in list(self.scripts.find({'user_id': user_id}))]

    def update_script(self, user_id: UUID, script_id: UUID, content: bytes):
        pass

    def delete_script(self, script_id: UUID) -> int:
        result: DeleteResult = self.scripts.delete_one({'_id': script_id})
        return result.deleted_count

script_store = UserStore('10.6.1.74', 'root', 'rootpassword')

if __name__ == '__main__':
    res = script_store.get_script(UUID('e32d478f-e305-4a74-94dc-47234d17d959'))
    print(res)
