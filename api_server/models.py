import datetime
from typing import Union

from pydantic import BaseModel


class SessionModel(BaseModel):
    start_time: datetime.datetime
    finish_time: datetime.datetime
    duration_sec: int
    station: str
    status: str


class RegisterSessionModel(BaseModel):
    sat_name: str
    session_list: list[SessionModel]
    user_script: str


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
    ...


class UserSatelliteModel(BaseModel):
    userId: int
    user_script: str
    sat_name: str
    radio_config: Union[LoRaConfig, FSK_Config]


class TaskModel(BaseModel):
    user_data: UserSatelliteModel
    start_time: datetime.datetime
    end_time: datetime.datetime
    status: str = 'pending'


class RotatorAxis(BaseModel):
    angle: float = 0
    speed: float = 0.7
    acceleration: float = 0.1
    min_angle: float = 0
    max_angle: float = 360
    # calibration: float


class RotatorModel(BaseModel):
    az: RotatorAxis
    el: RotatorAxis = {'angle': 0, 'speed': 0.7, 'acceleration': 0.1, 'max_angle': 90, 'min_angle': 0}


if __name__ == '__main__':
    m = TaskModel()
    print(m)