from __future__ import annotations
from datetime import datetime, timedelta
import random

from pytz import utc
# from uuid import UUID

# from devtools import debug

from api_server.sessions_store.time_range import TimeRange, merge


class TerminalTimeRange(TimeRange):
    symbol_list: list[str] = ['@', '#', '$', '%', '^', '&', '*', '-', '=', '~', 'o', '+', '0', "\"", "/", "v", "x",
                              "u", "w"]

    def __init__(self, start: datetime, **kwargs) -> None:
        super().__init__(start, **kwargs)
        self.symbol: str = kwargs.get('symbol', random.choice(self.symbol_list))

    def graphical_view(self) -> str:
        space = ' '
        start = datetime.now().astimezone(utc)
        return f'{space * ((self.start - start).seconds)}|{self.symbol*(self.duration_sec - 1)}| p={self.priority}'

def terminal_print(tr_list: list[TimeRange]) -> None:
    for tr in tr_list:
        if isinstance(tr, TimeRange):
            if not isinstance(tr, TerminalTimeRange):
                terminal_tr: TerminalTimeRange = TerminalTimeRange(**tr.dict())
                print(terminal_tr.graphical_view())
            else:
                print(tr.graphical_view())


if __name__ == '__main__':
    start_time: datetime = datetime.now()
    t_1: TerminalTimeRange = TerminalTimeRange(start=start_time + timedelta(seconds=5), duration_sec=20, priority=2)
    t_2: TerminalTimeRange = TerminalTimeRange(start=start_time + timedelta(seconds=1), duration_sec=10, priority=3)
    t_3: TerminalTimeRange = TerminalTimeRange(start=start_time + timedelta(seconds=1), duration_sec=30, priority=1)
    t_4: TerminalTimeRange = TerminalTimeRange(start=start_time + timedelta(seconds=5), duration_sec=26, priority=2)
    t_5: TerminalTimeRange = TerminalTimeRange(start=start_time + timedelta(seconds=45), duration_sec=5, priority=5)
    t_6: TerminalTimeRange = TerminalTimeRange(start=start_time + timedelta(seconds=12), duration_sec=5, priority=1)
    t_7: TerminalTimeRange = TerminalTimeRange(start=start_time + timedelta(seconds=42), duration_sec=25, priority=1)
    t_8: TerminalTimeRange = TerminalTimeRange(start=start_time + timedelta(seconds=55), duration_sec=5, priority=5)

    res = merge([t_1, t_2, t_3, t_4, t_5, t_6, t_7, t_8])
    terminal_print([t_1, t_2, t_3, t_4, t_5, t_6, t_7, t_8])
    print('----------------------------------------------------')
    terminal_print(res)  # type: ignore
