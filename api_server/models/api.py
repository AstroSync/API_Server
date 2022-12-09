
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TimeRangeModel(BaseModel):
    priority: int
    start: datetime
    duration_sec: int


class RegisterSessionModel(BaseModel):
    """
    Fields:
        user_id: UUID
        username: str
        sat_name: str
        priority: int
        start: datetime
        duration_sec: int
    Args:
        BaseModel (_type_): _description_
    """
    user_id: UUID
    username: str
    script_id: UUID
    sat_name: str
    priority: int
    start: datetime
    duration_sec: int

class SessionModel(BaseModel):
    start_time: datetime
    finish_time: datetime
    available_sec: int  # duration
    busy_sec: int
    station: str
    script_id: UUID
    priority: int

class RotatorAxis(BaseModel):
    position: float = 0
    speed: float = 2
    acceleration: float = 1
    boundary_start: float = -175
    boundary_end: float = 515
    limits: bool = True
    # calibration: float


class RotatorModel(BaseModel):
    az: RotatorAxis
    el: RotatorAxis = {'position': 0, 'speed': 2, 'acceleration': 1,
                       'boundary_start': -90, 'boundary_end': 270, 'limits': True}  # type: ignore
