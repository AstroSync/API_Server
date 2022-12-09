from __future__ import annotations
from datetime import datetime
# from hashlib import _Hash, sha1
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class UserDataModel(BaseModel):
    _id: UUID
    satellites: list[str]
    scripts: list[UUID]
    waiting_sessions: list[UUID]
    passed_sessions: list[UUID]
    priority_counter: int


class UserScriptModel(BaseModel):
    script_id: UUID = Field(default_factory=uuid4, alias='_id')
    user_id: UUID
    username: str
    script_name: str
    description: str = ''
    content: bytes
    upload_date: datetime
    last_edited_date: datetime
    size: int
    sha256: str

class SessionModel(BaseModel):
    user_id: UUID
    username: str
    script_id: UUID | None
    sat_name: str
    station: str
    status: str
    registration_time: datetime
    result: str
    traceback: str
    time_range_id: UUID
    priority: int
    start: datetime
    duration_sec: int
    finish: datetime
    parts: int
    initial_start: datetime
    initial_duration_sec: int

class ResultSessionModel(BaseModel):
    user_id: UUID
    username: str
    script_id: UUID | None
    sat_name: str
    station: str
    registration_time: datetime
    start_time: datetime
    duration_sec: int
    priority: int
    result: list = []
    traceback: str = ''



# class DbTaskModel(BaseModel):
#     _id: UUID
#     user_id: UUID
#     username: str
#     script_id: UUID | None
#     sat_name: str
#     registration_time: datetime
#     time_range: TimeRangeModel
#     # priority: int
#     # start: datetime
#     # duration_sec: int
#     # initial_start: datetime
#     # initial_duration_sec: int
#     # parts: int
#     station: str
#     status: str
#     result: str
#     traceback: str


class TimeRangeModel(BaseModel):
    _id: UUID = Field(..., alias="_id")
    priority: int
    start: datetime
    duration_sec: int
    parts: int
    initial_start: datetime
    initial_duration_sec: int
    # piwlp: list[UUID]
    # piwhp: list[UUID]
    # fiwlp: list[UUID]
    # covered_by: UUID | None


class LoRaConfig(BaseModel):
    coding_rate: str
    frequency: float
    bandwidth: str
    spreading_factor: int
    tx_power: int
    sync_word: int
    preamble_length: int
    auto_gain_control: bool
    payload_size: int
    lna_gain: int
    lna_boost: bool
    implicit_mode: bool
    rx_timeout: int


class FSK_Config(BaseModel):
    frequency: float


class UserSatelliteModel(BaseModel):
    userId: int
    user_script: str
    sat_name: str
    radio_config: LoRaConfig | FSK_Config

class Model2(BaseModel):
    c: int = 2

class Model(BaseModel):
    a: int = 1
    b: Model2 = Model2()

# if __name__ == '__main__':
#     m = TaskModel()
#     print(m)