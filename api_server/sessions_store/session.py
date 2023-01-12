from __future__ import annotations
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo
# from devtools import debug
from api_server.sessions_store.terminal_time_range import terminal_print
# from api_server.db_models import DbTaskModel
from api_server.sessions_store.time_range import TimeRange, merge


class Session(TimeRange):
    user_id: UUID
    username: str
    script_id: UUID | None
    sat_name: str
    station: str
    status: str  # Waiting / Process / Finished / Failed
    registration_time: datetime
    result: str
    traceback: str

    def __init__(self, username: str, start: datetime, **kwargs) -> None:
        super().__init__(start=start, **kwargs)
        self.user_id: UUID = kwargs.get('user_id', uuid4())
        self.username: str = username
        self.script_id: UUID | None = kwargs.get('script_id', None)
        self.sat_name: str = kwargs.get('sat_name', 'NORBI')
        self.station: str = kwargs.get('station', 'NSU')
        self.status: str = kwargs.get('status', 'WAITING')
        self.registration_time: datetime = kwargs.get('registration_time', datetime.utcnow()).astimezone(tz=ZoneInfo('UTC'))
        self.result: str = kwargs.get('result', '')
        self.traceback: str = kwargs.get('traceback', '')

    def relative_complement(self, val):
        if hasattr(val, 'station'):
            if self.station == val.station:  # type: ignore
                return super().relative_complement(val)
        return self
    # def convert_to_db_model(self) -> DbTaskModel:
    #     return DbTaskModel.parse_obj(self.__dict__)


if __name__ == '__main__':
    start_time: datetime = datetime.now() + timedelta(seconds=2)
    s1: Session = Session(username='lolkek', start=start_time, duration_sec=10, priority=1)
    s2: Session = Session(username='gdfg', start=start_time + timedelta(seconds=2),  duration_sec=5, priority=2)
    data: list[Session] = [s1, s2]
    # terminal_print(data)  # type: ignore
    new_data: list[TimeRange] = merge(data) # type: ignore
    print('-----------------')
    terminal_print(new_data)
    # print(s2.convert_to_db_model())
    # debug(s2.convert_to_db_model())
