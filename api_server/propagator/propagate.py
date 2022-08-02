from __future__ import annotations

import copy
import datetime
import os
import time
from datetime import date, datetime
from typing import Optional, Any, Type

from dateutil import parser
from pytz import utc
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite
from skyfield.timelib import Timescale, Time
from skyfield.toposlib import wgs84

observers = {
    'Новосибирск': wgs84.latlon(54.842625, 83.095025, 170),
    # 'Красноярск': wgs84.latlon(56.010041, 92.852069),
    # 'Москва': wgs84.latlon(55.4507, 37.3656)
}

satellites: list[EarthSatellite] = load.tle_file(os.path.join(os.path.dirname(__file__), 'cubesat_tle.txt'))


def get_sat_from_tle(name: str) -> Optional[EarthSatellite]:
    start_time = time.time()
    try:
        cubesat: EarthSatellite = list(filter(lambda sat: sat.name == name, satellites))[0]
    except IndexError:
        return None
    print(f"Tle loading took {time.time() - start_time} seconds")
    return cubesat


def get_sessions_for_sat(sat_name: str, t1: date | str,
                         t2: Optional[date | str] = None) -> list[dict[str, Any]] | Type[ValueError]:
    satellite = get_sat_from_tle(sat_name.upper())
    if satellite is None:
        return ValueError
    start_time = time.time()
    events_list_for_all_observers: dict[str, list[dict[str, datetime | int | str]]] = {}
    if type(t1) != type(t2):
        raise TypeError('Start and finish times have to have same types.')
    if type(t1) == str:
        t1 = parser.parse(t1)
    if type(t2) == str:
        t2 = parser.parse(t2)
    if t2 is None:
        t2 = load.timescale().from_datetime(datetime.combine(t1, datetime.max.time(), tzinfo=utc))
    elif t2 == t1:
        t2 = load.timescale().from_datetime(datetime.combine(t2, datetime.max.time(), tzinfo=utc))
    else:
        t2 = load.timescale().from_datetime(datetime.combine(t2, datetime.min.time(), tzinfo=utc))
    t1 = load.timescale().from_datetime(datetime.combine(t1, datetime.now().time(), tzinfo=utc))

    observers = {'Новосибирск': wgs84.latlon(54.842625, 83.095025, 170),
                 'Красноярск': wgs84.latlon(56.010041, 92.852069),
                 'Москва': wgs84.latlon(55.4507, 37.3656)}
    for location_name, observer in observers.items():
        event_time_list, event_type_list = satellite.find_events(observer, t1, t2, altitude_degrees=9)
        if len(event_type_list) > 1:  # there is at least one available session
            while event_type_list[0] != 0:  # skip events until start
                event_type_list: list[int] = event_type_list[1:]
                event_time_list: list[Time] = event_time_list[1:]
                if len(event_type_list) == 0:
                    break
            if len(event_type_list) == 0:
                continue

            event_dict: dict[str, datetime | int | str] = {}
            event_dict_list: list[dict[str, datetime | int | str]] = []
            for event_type, event_time in zip(event_type_list, event_time_list):
                if event_type == 0:
                    event_dict['start_time'] = event_time.astimezone(utc)
                elif event_type == 2:
                    event_dict['finish_time'] = event_time.astimezone(utc)
                    event_dict['duration_sec'] = (event_dict['finish_time'] - event_dict['start_time']).seconds
                    event_dict['finish_time'] = str(event_dict['finish_time'])
                    event_dict['start_time'] = str(event_dict['start_time'])
                    event_dict['station'] = location_name
                    # TODO: проверить в БД наличие такого сеанса. Если есть совпадение, то пометить как 'Busy'
                    #  возможно, стоит сделать отдельную функцию для выявления занятых сеансов из уже посчитанных.
                    event_dict['status'] = 'Available'  # Неопределен
                    event_dict_list.append(copy.copy(event_dict))
            events_list_for_all_observers[location_name] = event_dict_list
    # final_dict_list = [dict_array for dict_array in events_list_for_all_observers.values()]
    united_dicts = [value for internal_list in events_list_for_all_observers.values() for value in internal_list]
    print(f"Took {time.time() - start_time} seconds")
    print(f'united_dicts: {united_dicts}')
    return united_dicts


# points_time_list = ts.utc(t1.year, t1.month, t1.day, t1.hour, t1.minute, np.arange(0, (t2 - t1).seconds, per_n_sec))


def rotator_track(sat: str, observer: str, t1: datetime, t2: datetime = None, per_n_sec=1) -> tuple[
    list[float], list[float], list[Timescale]]:
    ts = load.timescale()
    start_time = time.time()
    points_time_list = ts.linspace(ts.from_datetime(t1), ts.from_datetime(t2), (t2 - t1).seconds // per_n_sec)
    topocentric = (get_sat_from_tle(sat) - observers[observer]).at(points_time_list)
    alt, az, distance = topocentric.altaz()
    print(f"Propagation took {time.time() - start_time} seconds")

    return alt.degrees, az.degrees, points_time_list.utc_datetime()


if __name__ == '__main__':
    # print(datetime(2022, 6, 20, 10, 10, 10, 0, utc))
    sessions = get_sessions_for_sat('NORBI', '19.06.2022', '19.06.2022')
    print('response:', sessions, len(sessions))

    # start_time = datetime(2022, 4, 15, 19, 5, 0, tzinfo=timezone.utc)
    # alt, az, t = rotator_track('NORBI', 'Новосибирск', start_time, start_time + timedelta(seconds=480), per_n_sec=10)
    # print(alt, az, t)
    # print(np.gradient(az))
