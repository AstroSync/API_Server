from __future__ import annotations
from datetime import datetime, timedelta
import uuid
from api_server.sessions_manager.difference_analizer import analize_difference
from api_server.sessions_manager.terminal_time_range import TerminalTimeRange, terminal_print
from api_server.sessions_manager.time_range import merge, TimeRange


class TimeRangesStore:
    def __init__(self) -> None:
        self.origin_ranges: list[TimeRange] = []  # unmerged ranges
        self.prev_merge: list[TimeRange] = []
        self.schedule: list[TimeRange] = []  # calculated priority ranges

    def _change_state(self) -> None:
        merged_ranges: list[TimeRange] = merge(self.origin_ranges)
        if len(self.prev_merge) == 0 and len(self.schedule) == 0:
            self.prev_merge[:] = merged_ranges[:]
            self.schedule[:] = merged_ranges[:]
        else:
            self.prev_merge[:] = self.schedule[:]
            self.schedule[:] = merged_ranges[:]

    def append(self, *time_ranges: TimeRange) -> None:
        self.origin_ranges.extend(time_ranges)
        self._change_state()
        analize_difference(self.prev_merge, self.schedule, time_ranges)

    def remove(self, *element: TimeRange) -> None:
        self.simple_remove()
        analize_difference(self.prev_merge, self.schedule, None, element)  # type: ignore

    def simple_remove(self, *element: TimeRange) -> None:
        if len(self.origin_ranges) == 0:
            raise ValueError('You can not remove element from empty list.')
        for el in element:
            self.origin_ranges.remove(el)
        self._change_state()

    def get_next(self, collection: list) -> TimeRange | None:
        if len(collection) > 0:
            next_time_range: TimeRange = collection[0]
            for time_range in collection:
                if time_range.start < next_time_range.start:
                    next_time_range = time_range
                return next_time_range
        return None


if __name__ == '__main__':
    TimeRanges_store = TimeRangesStore()

    start_time: datetime = datetime.now()

    t_1: TerminalTimeRange = TerminalTimeRange(time_range_id=uuid.UUID('10000000-0f28-4ed1-bae8-8243c4ea9443'),
                                               start=start_time + timedelta(seconds=5),
                                               duration_sec=20,
                                               priority=2)
    t_2: TerminalTimeRange = TerminalTimeRange(time_range_id=uuid.UUID('20000000-0f28-4ed1-bae8-8243c4ea9443'),
                                               start=start_time + timedelta(seconds=1),
                                               duration_sec=10,
                                               priority=3)
    t_3: TerminalTimeRange = TerminalTimeRange(time_range_id=uuid.UUID('30000000-0f28-4ed1-bae8-8243c4ea9443'),
                                               start=start_time + timedelta(seconds=1),
                                               duration_sec=30,
                                               priority=1)
    t_4: TerminalTimeRange = TerminalTimeRange(time_range_id=uuid.UUID('40000000-0f28-4ed1-bae8-8243c4ea9443'),
                                               start=start_time + timedelta(seconds=5),
                                               duration_sec=26,
                                               priority=2)
    t_5: TerminalTimeRange = TerminalTimeRange(time_range_id=uuid.UUID('50000000-0f28-4ed1-bae8-8243c4ea9443'),
                                               start=start_time + timedelta(seconds=40),
                                               duration_sec=15,
                                               priority=5)
    t_6: TerminalTimeRange = TerminalTimeRange(time_range_id=uuid.UUID('60000000-0f28-4ed1-bae8-8243c4ea9443'),
                                               start=start_time + timedelta(seconds=12),
                                               duration_sec=5,
                                               priority=1)
    t_7: TerminalTimeRange = TerminalTimeRange(time_range_id=uuid.UUID('70000000-0f28-4ed1-bae8-8243c4ea9443'),
                                               start=start_time + timedelta(seconds=42),
                                               duration_sec=25,
                                               priority=1)
    t_8: TerminalTimeRange = TerminalTimeRange(time_range_id=uuid.UUID('80000000-0f28-4ed1-bae8-8243c4ea9443'),
                                               start=start_time + timedelta(seconds=55),
                                               duration_sec=5,
                                               priority=5)

    TimeRanges_store.append(t_2, t_3)
    TimeRanges_store.append(t_1)

    TimeRanges_store.append(t_7)

    TimeRanges_store.append(t_4, t_6, t_8)
    TimeRanges_store.append(t_5)
    # TimeRanges_store.remove(t_2, t_4, t_7)
    print('-------------------- ORIGIN --------------------------')
    terminal_print(TimeRanges_store.origin_ranges)  # type: ignore
    print('------------------- SCHEDULE -------------------------')
    terminal_print(TimeRanges_store.schedule)  # type: ignore
    print('--------------------- Prev ---------------------------')
    terminal_print(TimeRanges_store.prev_merge)  # type: ignore

