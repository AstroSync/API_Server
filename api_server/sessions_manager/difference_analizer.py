from __future__ import annotations

from typing import Iterable
import uuid
from api_server.sessions_manager.time_range import TimeRange


def analize_difference(prev_merge: list[TimeRange], schedule: list[TimeRange],
                       new_ranges: tuple[TimeRange] | list[TimeRange] | TimeRange | None = None,
                       removed_ranges: tuple[TimeRange] | list[TimeRange] | TimeRange | None = None):
    """

    Args:
        prev_merge (list[TimeRange]): Результат слияния списка интервалов raw_prev_merge.
        current_merge (list[TimeRange]): Результат слияния raw_prev_merge + new_ranges, который хотим проанализировать.
        new_ranges (list[TimeRange] | None): Список интервалов, что были добавлены в последнем слиянии.
        removed_ranges (list[TimeRange] | None): Список интервалов, что должны были быть удалены.

    Raises:
        ValueError: Если в removed_ranges есть элемент, которого нет в prev_merge. В таком случае, возможно есть
                    проблемы с согласованностью.
        ValueError: Если элемент из new_ranges есть в prev_merge. Система не должна пытаться зарегистрировать сеанс,
                    который уже был зарегистрирован. Вероятно, список составлен неверно.
    """
    print('\nAnalazing...\n')
    if new_ranges is None:
        new_ranges = []
    if removed_ranges is None:
        removed_ranges = []
    if not isinstance(new_ranges, Iterable):
        analize_append(schedule=schedule, new_ranges=[new_ranges])
    else:
        analize_append(schedule=schedule, new_ranges=list(new_ranges))
    if not isinstance(removed_ranges, Iterable):
        analize_remove(prev_merge=prev_merge, schedule=schedule, removed_ranges=[removed_ranges])
    else:
        analize_remove(prev_merge=prev_merge, schedule=schedule, removed_ranges=list(removed_ranges))


def analize_append(schedule: list[TimeRange], new_ranges: list[TimeRange]):
    schedule_idlist: list[uuid.UUID] = [time_range.get_id() for time_range in schedule]
    for time_range in new_ranges:
        # if time_range.get_id() in prev__idlist:
        #     raise ValueError(f'New element can not be in pre_merge and new_ranges lists simultaneously\n{time_range}')
        if time_range.get_id() in schedule_idlist:
            merged_elements: list[TimeRange] = get_time_range_by_id(schedule, time_range.get_id())
            if len(merged_elements) == 1:
                if merged_elements[0].duration_sec < time_range.duration_sec:
                    print(f'New element lost part {time_range.duration_sec - merged_elements[0].duration_sec} sec.\n'\
                          f'{merged_elements[0]}')
                else:
                    print(f'New element was successfully added.\n{time_range}')
            elif len(merged_elements) > 1:
                print(f'New element was splitted to {len(merged_elements)} parts.')
        else:
            print(f'Another element from new_ranges or prev_merge fully covers and has higher priority.\n{time_range}')


def analize_remove(prev_merge: list[TimeRange], schedule: list[TimeRange], removed_ranges: list[TimeRange]):
    schedule_idlist: list[uuid.UUID] = [time_range.get_id() for time_range in schedule]
    prev_idlist: list[uuid.UUID] = [time_range.get_id() for time_range in prev_merge]
    removed_counter = 0
    for removed_range in removed_ranges:
        # Элемент удаляется из raw_prev_merge и после слияния получаем current_merge но уже без этого элемента
        # Далее сравниваем два результата слияния с элементом и без него.
        if removed_range.get_id() in prev_idlist:
            removed_counter += 1
    print(f'Will be removed {removed_counter} ranges.')
            # raise ValueError(f'TimeRange from removed_ranges list was never registered.\n{removed_range}')
    for prev_merged_element in prev_merge:
        if prev_merged_element.get_id() not in schedule_idlist:
            print(f'Prev_merge element was fully covered by new element. Deleted element:\n{prev_merged_element}')
        else:
            schedule_element_parts: list[TimeRange] = get_time_range_by_id(schedule, prev_merged_element.get_id())
            prev_merged_element_parts: list[TimeRange] = get_time_range_by_id(prev_merge, prev_merged_element.get_id())
            if len(prev_merged_element_parts) < len(schedule_element_parts):
                print(f'Prev_merge element was splitted to {len(schedule_element_parts)} parts.')
                # new_elements = [el for el in prev_merged_element_parts if el not in schedule_element_parts]
                # print(f'{new_elements=}')
            elif len(prev_merged_element_parts) > len(schedule_element_parts):
                if prev_merged_element not in schedule:  # подумать над введением id для отдельных частей
                    print(f'Prev_merge part of element was fully covered by new element with higher priority.')
                    print(prev_merged_element)


def get_time_range_by_id(ranges_list: list[TimeRange], range_id: uuid.UUID) -> list[TimeRange]:
    return [el for el in ranges_list if el.get_id() == range_id]
