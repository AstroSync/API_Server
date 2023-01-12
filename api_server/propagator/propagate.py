from __future__ import annotations

import os
import time
from datetime import date, datetime, timezone
import numpy as np
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite
from skyfield.timelib import Time, Timescale
from skyfield.toposlib import wgs84
from skyfield.toposlib import GeographicPosition



OBSERVERS: dict[str, GeographicPosition] = {'NSU': wgs84.latlon(54.842625, 83.095025, 170),
                                            # 'Красноярск': wgs84.latlon(56.010041, 92.852069),
                                            # 'Москва': wgs84.latlon(55.4507, 37.3656)
                                            }

satellites: list[EarthSatellite] = load.tle_file(os.path.join(os.path.dirname(__file__), 'cubesat_tle.txt'))


def get_sat_from_local_tle_file(name: str) -> EarthSatellite | None:
    start_time: float = time.time()
    try:
        # cubesat: EarthSatellite = list(filter(lambda sat: sat.name == name, satellites))[0]
        cubesat: EarthSatellite = [sat for sat in satellites if sat.name == name][0]
    except IndexError:
        return None
    print(f"Tle loading took {time.time() - start_time} seconds")
    return cubesat


def request_celestrak_sat_tle(sat_name: str) -> EarthSatellite | None:
    start_time: float = time.time()
    try:
        url: str = f"https://celestrak.org/NORAD/elements/gp.php?NAME={sat_name}".replace(' ', '%20')
        cubesat: EarthSatellite = load.tle_file(url, reload=True)[0]
    except IndexError:
        return None
    print(f"Tle loading took {time.time() - start_time} seconds")
    print(f'cubesat: {cubesat}')
    return cubesat


def convert_time_args(t_1: date | str, t_2: date | str | None = None) -> tuple[Time, Time]:
    """As the frontend pass time arguments in different format, they need to be convertet datetime and
    then to Timescale. This function is auxiliary function for get_sessions_for_sat().

    Args:
        t_1 (date): start time of popagetion
        t_2 (Optional[date, str]): finish time of propagetion. Defaults to None.
                                   None supposed to calculate session for 1 day since t_1 time.

    Returns:
        tuple[Timescale, Timescale]: converted time values for skyfield propagation.
    """
    timescale: Timescale = load.timescale()
    if isinstance(t_1, str):
        t_1 = date.fromisoformat(t_1)
    if isinstance(t_2, str):
        t_2 = date.fromisoformat(t_2)
    if t_2 is None:
        t_2_ts: Time = timescale.from_datetime(datetime.combine(t_1, datetime.max.time(), tzinfo=timezone.utc))
    elif t_2 == t_1:
        t_2_ts: Time = timescale.from_datetime(datetime.combine(t_2, datetime.max.time(), tzinfo=timezone.utc))
    else:
        t_2_ts: Time = timescale.from_datetime(datetime.combine(t_2, datetime.min.time(), tzinfo=timezone.utc))
    t_1_ts: Time = timescale.from_datetime(datetime.combine(t_1, datetime.utcnow().time(), tzinfo=timezone.utc))
    return t_1_ts, t_2_ts


def skip_events_until_start(event_type_list: list[int], event_time_list: Time) -> tuple[list[int], Time]:
    """Some times propagation may start at moment, when the satellite already at observation point.
    We will skip this session and wait next.

    Args:
        event_type_list (list[int]): List of event numbers,
                                     where 0 - rise above horizone, 1 - culminate, 2 - set below horizone
        event_time_list (list[Time]): Corresponding time points for events.

    Returns:
        tuple[list[int], list[Time]]: Event list without already running session.
    """
    new_event_type_list: list[int] = event_type_list
    new_event_time_list: Time = event_time_list
    while event_type_list[0] != 0:
        new_event_type_list = event_type_list[1:]
        new_event_time_list = event_time_list[1:]
        if len(event_type_list) == 0:
            break
    return new_event_type_list, new_event_time_list


def map_events(event_type_list: list[int], event_time_list: Time, location_name: str) -> list[dict]:
    """ Функция разметки событий спутника. После фильтрации сюда гарантированно попадают события, начинающиеся с 0.
    Args:
        event_type_list (list[int]): List of event numbers,
                                     where 0 - rise above horizone, 1 - culminate, 2 - set below horizone
        event_time_list (Time): Corresponding time points for events.
        location_name (str): Observation point name

    Returns:
        list[dict]: _description_
    """
    event_dict_list: list[dict[str, int | str]] = []
    event_tupples = zip(np.array_split(event_type_list, 3), np.array_split(event_time_list, 3)) # type: ignore
    for event_list, (start, _, finish) in event_tupples:
        if len(event_list) == 3:
            event_dict: dict[str, int | str] = {'duration_sec': (finish - start).seconds,
                                                'finish_time': finish.astimezone(timezone.utc).isoformat(' ', 'seconds'),
                                                'start_time': start.astimezone(timezone.utc).isoformat(' ', 'seconds'),
                                                'station': location_name}
            event_dict_list.append(event_dict)
    return event_dict_list


def events_for_observers(satellite: EarthSatellite, observers: dict, ts_1: Time, ts_2: Time) -> tuple[dict, list[dict]]:
    events_list_for_all_observers: dict[str, list[dict[str, datetime | int | str]]] = {}
    event_dict_list: list[dict] = []
    for location_name, observer in observers.items():
        sat_events: tuple[Time, list[int]] = satellite.find_events(observer, ts_1, ts_2, altitude_degrees=3)  # type: ignore
        event_type_list: list[int] = sat_events[1]
        event_time_list: Time = sat_events[0]
        if len(event_type_list) > 1:  # there is at least one available session
            filtered_events, filtered_event_times = skip_events_until_start(event_type_list, event_time_list)
            if len(filtered_events) == 0:
                continue
            event_dict_list: list[dict] = map_events(filtered_events, filtered_event_times, location_name)
            events_list_for_all_observers[location_name] = event_dict_list
    return events_list_for_all_observers, event_dict_list


def download_tle(sat_name: str, local_tle: bool) -> EarthSatellite:
    if local_tle:
        satellite: EarthSatellite | None = get_sat_from_local_tle_file(sat_name.upper())
    else:
        satellite = request_celestrak_sat_tle(sat_name.upper())

    if satellite is None:
        raise ValueError('No satellite tle data')
    return satellite


def get_sessions_for_sat(sat_name: str, observers: dict, t_1: date | str, t_2: date | str | None = None,
                         local_tle: bool = True) -> tuple[list[dict], dict[str, list[dict]]]:
    satellite: EarthSatellite = download_tle(sat_name, local_tle)
    ts_1, ts_2 = convert_time_args(t_1, t_2)
    grouped_dicts: dict[str, list[dict]]
    flat_dicts : list[dict]
    grouped_dicts, flat_dicts = events_for_observers(satellite, observers, ts_1, ts_2)
    print(f'united_dicts: {flat_dicts}')
    # print(f'grouped_dicts: {grouped_dicts}')
    return flat_dicts, grouped_dicts


if __name__ == '__main__':
    # # print(datetime(2022, 6, 20, 10, 10, 10, 0, utc))
    sessions = get_sessions_for_sat('NORBI', OBSERVERS, '2022-12-30', '2022-12-31')
    # # print('response:', sessions, len(sessions))
    # # print(request_celestrak_sat_tle('NORBI'))

    # print(convert_degrees(np.array([*np.arange(350, 359), *np.arange(0, 9)])))
    # print(convert_degrees(np.array([*np.arange(9, 0, -1), *np.arange(359, 350, -1)])))

    # print(request_celestrak_sat_tle('NORBI'))
    # print(get_sessions_for_sat('NORBI', OBSERVERS, datetime.today()))

