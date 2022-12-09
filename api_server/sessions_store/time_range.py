from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Iterable, Union
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo
from rich.pretty import pprint
class EmptyRange:
    def __sub__(self, val: TimeRange | EmptyRange) -> TimeRange | EmptyRange:  # type: ignore
        if isinstance(val, EmptyRange):
            return self
        return val
    def __str__(self) -> str:
        return 'EmptyRange'

class PrettyPrint:
    def __str__(self) -> str:
        lines: list[str] = [self.__class__.__name__ + ':']
        for key, val in vars(self).items():
            lines += f'{key}: {val}'.split('\n')
        return '\n    '.join(lines)

class Intersections(PrettyPrint):
    def __init__(self, **kwargs) -> None:
        self.piwlp: list[UUID] = kwargs.get('piwlp', [])  # partically intersections with lower priority
        self.piwhp: list[UUID] = kwargs.get('piwhp', [])  # partically intersections with higher priority
        self.fiwlp: list[UUID] = kwargs.get('fiwlp', [])  # fully intersections with lower priority
        self.covered_by: UUID | None = kwargs.get('covered_by', None)

class TimeRange(PrettyPrint):
    time_range_id: UUID
    priority: int
    start: datetime
    duration_sec: int
    finish: datetime
    parts: int
    initial_start: datetime
    initial_duration_sec: int

    def __init__(self, start: datetime, **kwargs) -> None:
        self.time_range_id: UUID = kwargs.get('time_range_id', uuid4())
        self.priority: int = kwargs.get('priority', 1)
        self.start: datetime = start.astimezone(tz=ZoneInfo('UTC'))
        self.duration_sec: int = kwargs.get('duration_sec', 0)
        self.finish: datetime = kwargs.get('finish', self.start + timedelta(seconds=self.duration_sec)).astimezone(tz=ZoneInfo('UTC'))
        if self.finish == self.start:
            raise ValueError('Use EmptyRange')
        if self.start > self.finish:
            raise ValueError('Incorrect TimeRange format: start later then finish.')
        self.duration_sec = (self.finish - self.start).seconds
        self.parts: int = kwargs.get('parts', 1)
        self.initial_start: datetime = kwargs.get('initial_start', start).astimezone(tz=ZoneInfo('UTC'))
        self.initial_duration_sec: int = kwargs.get('initial_duration_sec', self.duration_sec)
        # self.piwlp: list[UUID] = kwargs.get('piwlp', [])  # partically intersections with lower priority
        # self.piwhp: list[UUID] = kwargs.get('piwhp', [])  # partically intersections with higher priority
        # self.fiwlp: list[UUID] = kwargs.get('fiwlp', [])  # fully intersections with lower priority
        # self.covered_by: UUID | None = kwargs.get('covered_by', None)

    def __eq__(self, val: TimeRange | EmptyRange) -> bool:
        if isinstance(val, TimeRange):
            return self.time_range_id == val.time_range_id and self.priority == val.priority and \
                   self.start == val.start and self.finish == val.finish and self.duration_sec == val.duration_sec
        return False

    def __lt__(self, val: TimeRange) -> bool:
        return self.priority < val.priority

    def __gt__(self, val: TimeRange) -> bool:
        return self.priority > val.priority

    def __contains__(self, val: TimeRange) -> bool:
        """
        self:      |--------------|
        val:           |======|
        (val in self) = True
        """
        return val.start >= self.start and val.finish <= self.finish

    def get_id(self) -> UUID:
        return self.time_range_id

    def timedelta(self) -> timedelta:
        return self.finish - self.start

    def astimezone(self, tz: ZoneInfo) -> TimeRange:
        self.start.astimezone(tz)
        self.finish.astimezone(tz)
        return self

    def relative_complement(self, val: TimeRange | EmptyRange):
        """
        ###############################
        self:        |----------|
        val:              |=========|
        _______________________________
        res:         |----|

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        self:            |----------|
        val:       |=========|
        _______________________________
        res:                 |------|

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        self:       |--------------|
        val:            |====|
        _______________________________
        res:        |---|    |-----|

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        self:           |----|
        val:         |==========|
        _______________________________
        res:          EmptyRange

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        self:        |-----|
        val:                 |=====|
        _______________________________
        res:         |-----|
        """
        if isinstance(val, EmptyRange):
            return self
        intersection: TimeRange | EmptyRange = calc_intersect(self, val)
        finish: datetime = self.finish
        start: datetime = self.start
        if not isinstance(intersection, EmptyRange):
            if intersection.start > self.start and intersection.finish == self.finish:
                finish: datetime = intersection.start
            elif intersection.start == self.start and intersection.finish < self.finish:
                start: datetime = intersection.finish
            elif self in val:
                return EmptyRange()
            elif val in self:
                return (self.__class__(finish=val.start, **dict({k: v for k, v in self.__dict__.items() if k != 'finish'})),
                        self.__class__(start=val.finish, **dict({k: v for k, v in self.__dict__.items() if k != 'start'})))
        # partial or no intersection
        return self.__class__(start=start, finish=finish, **removekey(removekey(self.__dict__, 'start'), 'finish'))

    def dict(self) -> dict:
        return self.__dict__


def removekey(d, key):
    r = dict(d)
    del r[key]
    return r

def isintersection(t1: TimeRange | EmptyRange, t2: TimeRange | EmptyRange) -> bool:
    if isinstance(t1, EmptyRange) or isinstance(t2, EmptyRange):
        return False
    latest_start = max(t1.start, t2.start)
    earliest_end = min(t1.finish, t2.finish)
    return latest_start <= earliest_end


def calc_intersect(t1: TimeRange | EmptyRange, t2: TimeRange | EmptyRange) -> TimeRange | EmptyRange:
    """ Creates new instance of intersection t1 and t2
    INPUTS:
    t1:         |------------|
    t2:                |===========|
    _______________________________________
    intersec:          |#####|

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    t1:          |---------|
    t2:        |===============|
    _______________________________________
    intersec:    |#########|

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    t1:         |---------|
    t2:                      |=======|
    _______________________________________
    intersec:  EmptyRange
    """
    if isinstance(t1, EmptyRange) and not isinstance(t2, EmptyRange):
        return t2
    if not isinstance(t1, EmptyRange) and isinstance(t2, EmptyRange):
        return t1
    if isinstance(t1, EmptyRange) and isinstance(t2, EmptyRange):
        return EmptyRange()
    if not isinstance(t1, EmptyRange) and not isinstance(t2, EmptyRange) and isintersection(t1, t2):
        return TimeRange(start=max(t1.start, t2.start), finish=min(t1.finish, t2.finish))
    return EmptyRange()  # type: ignore


# def get_intersections(tr_list: list[TimeRange], time_range: TimeRange) -> Intersections:
#     intersections = Intersections()
#     for tr in tr_list:
#         relative_complement: RelativeComplement = tr.relative_complement(time_range)
#         if isinstance(relative_complement, EmptyRange):
#             intersections.covered_by = time_range.get_id()
#             time_range.fiwlp.append(comparable_range.get_id())
#         elif relative_complement != comparable_range:  # comparable_range was splitted or has an intersecion
#             comparable_range.piwhp.append(time_range.get_id())
#             time_range.piwlp.append(comparable_range.get_id())

RelativeComplement = Union[TimeRange, tuple[TimeRange, TimeRange], EmptyRange]


def merge(ranges_list: list[TimeRange]) -> list[TimeRange]:
    """ Immutable function.
    Отсортировав изначальный список интервалов по наибольшему приоритету мы сможем
    избежать ситуации, когда интервал с которым сравнивают будет раздроблен сравниваемым
    интервалом.

    Интервал, стоящий в списке раньше интервала с таким же значением приоритета считается
    более приоритетным и будет дробить следущие за ним интервалы.

    Остается поэлементно сравнить каждый интервал с остальными и посчитать их относительное
    дополнение. Результат относительного дополнения перезаписывает элемент в изначальном
    списке от которого был посчитан. При дроблении интервалов изначальный список будет
    расширяться.
    """
    result_list: list[TimeRange] = deepcopy(ranges_list)
    result_list.sort(reverse=True)  # sort by priority. Higher priority first
    for i, time_range in enumerate(result_list):
        for comparable_range in result_list[i + 1: ]:
            relative_complement: RelativeComplement = comparable_range.relative_complement(time_range)
            if isinstance(relative_complement, EmptyRange):
                result_list.remove(comparable_range)
            elif relative_complement != comparable_range:  # comparable_range was splitted or has an intersecion
                result_list[:] = list(replace(result_list, old_item=comparable_range, new_items=relative_complement))[:]
    recalculate_parts(result_list)  # after splitting ranges need to recalculate their 'parts' parameter
    return result_list  # sorted(result_list, key=lambda x: x.start, reverse=False)


def recalculate_parts(ranges_list: list[TimeRange]) -> None:
    id_list: list[UUID] = [val.get_id() for val in ranges_list]
    for val in ranges_list:
        val.parts = id_list.count(val.get_id())


def replace(origin_list: list, old_item: Any, new_items: Iterable | Any):
    for item in origin_list:
        if item == old_item:
            if isinstance(new_items, Iterable):
                for new_tem in new_items:
                    yield new_tem
            else:
                yield new_items
        else:
            yield item

if __name__ == '__main__':
    # print((zoneinfo.available_timezones()))
    start_time = datetime.now()
    t_1: TimeRange = TimeRange(start_time + timedelta(seconds=5), duration_sec=20, priority=2)
    t_2: TimeRange = TimeRange(start_time + timedelta(seconds=7), duration_sec=10, priority=3)
    res = merge([t_1, t_2])
    _ = [pprint(x.dict()) for x in res]
