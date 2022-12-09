from __future__ import annotations

import copy
import os
import time
from datetime import date, datetime, timedelta
from typing import Any, Optional, Literal
# from dateutil import parser
from datetime import timezone
from skyfield.api import load
from skyfield.sgp4lib import EarthSatellite
from skyfield.timelib import Time, Timescale
from skyfield.toposlib import wgs84
from skyfield.units import Angle, Distance, AngleRate, Velocity
from skyfield.vectorlib import VectorSum
from skyfield.positionlib import Geocentric
from skyfield.toposlib import GeographicPosition
import numpy as np


OBSERVERS: dict[str, GeographicPosition] = {'NSU': wgs84.latlon(54.842625, 83.095025, 170),
                                            # 'Красноярск': wgs84.latlon(56.010041, 92.852069),
                                            # 'Москва': wgs84.latlon(55.4507, 37.3656)
                                            }

satellites: list[EarthSatellite] = load.tle_file(os.path.join(os.path.dirname(__file__), 'cubesat_tle.txt'))


def get_sat_from_local_tle_file(name: str) -> Optional[EarthSatellite]:
    start_time: float = time.time()
    try:
        cubesat: EarthSatellite = list(filter(lambda sat: sat.name == name, satellites))[0]
    except IndexError:
        return None
    print(f"Tle loading took {time.time() - start_time} seconds")
    return cubesat


def request_celestrak_sat_tle(sat_name: str) -> EarthSatellite | None:
    start_time: float = time.time()
    try:
        cubesat: EarthSatellite = load.tle_file(f"https://celestrak.org/NORAD/elements/gp.php?NAME={sat_name}")[0]
    except IndexError:
        return None
    print(f"Tle loading took {time.time() - start_time} seconds")
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
    t_1_ts: Time = timescale.from_datetime(datetime.combine(t_1, datetime.now().time(), tzinfo=timezone.utc))
    return t_1_ts, t_2_ts


def skip_events_until_start(event_type_list: list[int], event_time_list: list[Time]) -> tuple[list[int], list[Time]]:
    """Some times propagation may start at moment, when the satellite already at observation point.
    We will skip this session and wait next.

    Args:
        event_type_list (list[int]): List of event numbers,
                                     where 0 - rise above horizone, 1 - culminate, 2 - set below horizone
        event_time_list (list[Time]): Corresponding time points for events.

    Returns:
        tuple[list[int], list[Time]]: Event list without already running session.
    """
    while event_type_list[0] != 0:
        event_type_list = event_type_list[1:]
        event_time_list = event_time_list[1:]
        if len(event_type_list) == 0:
            break
    return event_type_list, event_time_list


def map_events(event_type_list: list[int], event_time_list: list[Time], location_name: str):
    event_dict: dict[str, datetime | int | str] = {}
    event_dict_list: list[dict[str, datetime | int | str]] = []
    for event_type, event_time in zip(event_type_list, event_time_list):
        if event_type == 0:
            event_dict['start_time'] = event_time.astimezone(timezone.utc)  # type: ignore
        elif event_type == 2:
            event_dict['finish_time'] = event_time.astimezone(timezone.utc)  # type: ignore
            event_dict['duration_sec'] = (event_dict['finish_time'] - event_dict['start_time']).seconds  # type: ignore
            event_dict['finish_time'] = str(event_dict['finish_time'])
            event_dict['start_time'] = str(event_dict['start_time'])
            event_dict['station'] = location_name
            event_dict['status'] = 'Available'  # Неопределен
            event_dict_list.append(copy.copy(event_dict))
    return event_dict_list


def events_for_observers(satellite: EarthSatellite, observers: dict, ts_1: Time, ts_2: Time):
    events_list_for_all_observers: dict[str, list[dict[str, datetime | int | str]]] = {}
    for location_name, observer in observers.items():
        event_time_list, event_type_list = satellite.find_events(observer, ts_1, ts_2, altitude_degrees=3)
        if len(event_type_list) > 1:  # there is at least one available session
            event_type_list, event_time_list = skip_events_until_start(event_type_list, event_time_list)
            if len(event_type_list) == 0:
                continue
            event_dict_list = map_events(event_type_list, event_time_list, location_name)
            events_list_for_all_observers[location_name] = event_dict_list
    return events_list_for_all_observers


def get_sessions_for_sat(sat_name: str, observers: dict,
                         t_1: date | str, t_2: Optional[date | str] = None, local_tle: bool = True) -> list[dict[str, Any]]:
    satellite: EarthSatellite | None = get_sat_from_local_tle_file(sat_name.upper()) if local_tle else request_celestrak_sat_tle(sat_name.upper())
    if satellite is None:
        raise ValueError
    start_time: float = time.time()
    ts_1, ts_2 = convert_time_args(t_1, t_2)
    events_list_for_all_observers = events_for_observers(satellite, observers, ts_1, ts_2)
    # final_dict_list = [dict_array for dict_array in events_list_for_all_observers.values()]
    united_dicts = [value for internal_list in events_list_for_all_observers.values() for value in internal_list]
    print(f"Took {time.time() - start_time} seconds")
    print(f'united_dicts: {united_dicts}')
    return united_dicts


class SatellitePath:
    def __init__(self, altitude: Angle, azimute: Angle, distance: Distance,
                 alt_rate: AngleRate, az_rate: AngleRate, dist_rate: Velocity, time_points: list[datetime]) -> None:
        self.altitude: np.ndarray = altitude.degrees  # type: ignore
        self.azimuth: np.ndarray = azimute.degrees  # type: ignore
        self.dist: np.ndarray = distance.km  # type: ignore
        self.alt_rate: np.ndarray = alt_rate.degrees.per_second  # type: ignore
        self.az_rate: np.ndarray = az_rate.degrees.per_second  # type: ignore
        self.dist_rate: np.ndarray = dist_rate.km_per_s  # type: ignore
        self.t_points: list[datetime] = time_points
        self.__index: int = 0
        # 1 - 'up', -1 - 'down'
        self.az_rotation_direction: Literal[1, -1] = -1 + 2 * (self.azimuth[1] > self.azimuth[0])  # type: ignore

    def __repr__(self) -> str:
        return f'Altitude deg from {self.altitude[0]:.2f} to {self.altitude[-1]:.2f}\n' \
               f'Azimuth deg from {self.azimuth[0]:.2f} to {self.azimuth[-1]:.2f}\n' \
               f'Distance km from {self.dist.min():.2f} to {self.dist.max():.2f}\n' \
               f'Altitude rate deg/s from {self.alt_rate.min():.2f} to {self.alt_rate.max():.2f}\n' \
               f'Azimuth rate deg/s from {self.az_rate.min():.2f} to {self.az_rate.max():.2f}\n' \
               f'Distance rate km/s from {self.dist_rate.min():.2f} to {self.dist_rate.max():.2f}\n' \
               f'Time points: from {self.t_points[0]} to {self.t_points[-1]}.\n' \
               f'Duration: {(self.t_points[-1] - self.t_points[0]).seconds} sec\n'

    def __getitem__(self, key) -> tuple[float, float, datetime]:
        return (self.altitude.__getitem__(key), self.azimuth.__getitem__(key),
               self.t_points.__getitem__(key))

    def __iter__(self):
        return self

    def __next__(self) -> tuple[float, float, datetime]:
        if self.__index < len(self.altitude):
            var: tuple[float, float, datetime] = (self.altitude[self.__index], self.azimuth[self.__index],
                    self.t_points[self.__index])
            self.__index += 1
            return var
        raise StopIteration


class TestSatellitePath:

    def __init__(self, test_size: int = 45) -> None:
        self.altitude = np.linspace(0.0, test_size, num=test_size)
        self.azimuth = np.linspace(90.0, 90 + test_size, num=test_size)
        self.dist = np.zeros(test_size)
        self.alt_rate = np.ones(test_size)
        self.az_rate = np.ones(test_size)
        self.dist_rate = np.zeros(test_size)
        self.az_rotation_direction = 1
        self.t_points = [datetime.now(tz=timezone.utc) + timedelta(seconds=6 + x) for x in range(test_size)]
        self.__index: int = 0
    def __getitem__(self, key) -> tuple[float, float, datetime]:
        return (self.altitude.__getitem__(key), self.azimuth.__getitem__(key),
               self.t_points.__getitem__(key))

    def __iter__(self):
        return self

    def __next__(self) -> tuple[float, float, datetime]:
        if self.__index < len(self.altitude):
            var: tuple[float, float, datetime] = (self.altitude[self.__index], self.azimuth[self.__index],
                    self.t_points[self.__index])
            self.__index += 1
            return var
        raise StopIteration

# def convert_degrees(seq):
#     """Recalculate angle sequence when it transits over 360 degrees.
#     e.g.: [358.5, 359.6, 0.2, 1.1] -> [358.5, 359.6, 360.2, 361.1]
#           [1.1, 0.2, 359.6, 358.5] -> [1.1, 0.2, -0.4, -1.5]

#     Args:
#         seq (ndarray | list[float]): the sequence of angles

#     Raises:
#         RuntimeError: check origin sequence carefully when get this exception.
#         It raises when there are several transition over 360 degrees.

#     Returns:
#         [ndarray]: Origin sequence if there no transition over 360 degrees
#         else recalculated sequence as in example.
#     """
#     if isinstance(seq, list):
#         seq = np.array(seq)
#     diff = np.absolute(seq[1:] - seq[:-1])  # differences of neighboring elements
#     indices = np.where(diff > 300)[0]
#     if len(indices) > 1:
#         raise RuntimeError('Unbelievable shit happened!')
#     if len(indices) == 0:
#         return seq
#     return np.append(seq[:indices[0] + 1], seq[indices[0] + 1:] + 360 * (-1 + 2 * (seq[1] > seq[0])))



def angle_points_for_linspace_time(sat: str, observer: str, t_1: datetime, t_2: datetime,
                                   sampling_rate=3.3333, local_tle: bool = True) -> SatellitePath:
    timescale: Timescale = load.timescale()
    time_points: Time = timescale.linspace(timescale.from_datetime(t_1), timescale.from_datetime(t_2),
                                     int((t_2 - t_1).seconds * sampling_rate))
    satellite: EarthSatellite | None = get_sat_from_local_tle_file(sat.upper()) if local_tle else request_celestrak_sat_tle(sat.upper())
    if satellite is not None:
        sat_position: VectorSum = (satellite - OBSERVERS[observer])
    else:
        raise RuntimeError('Get incorrect sattelite')
    topocentric: Geocentric = sat_position.at(time_points)  # type: ignore
    return SatellitePath(*topocentric.frame_latlon_and_rates(OBSERVERS[observer]), time_points.utc_datetime())  # type: ignore


if __name__ == '__main__':
    # # print(datetime(2022, 6, 20, 10, 10, 10, 0, utc))
    # # sessions = get_sessions_for_sat('NORBI', '19.06.2022', '19.06.2022')
    # # print('response:', sessions, len(sessions))
    # # print(request_celestrak_sat_tle('NORBI'))
    start_time_: datetime = datetime.now(tz=timezone.utc)
    points: SatellitePath = angle_points_for_linspace_time('NORBI', 'NSU', start_time_, start_time_ + timedelta(seconds=4), local_tle=False)
    print(points)
    for alt, az, t_point in points:
        print(alt, az, t_point)

    # print(convert_degrees(np.array([*np.arange(350, 359), *np.arange(0, 9)])))
    # print(convert_degrees(np.array([*np.arange(9, 0, -1), *np.arange(359, 350, -1)])))

    # print(request_celestrak_sat_tle('NORBI'))
    # print(get_sessions_for_sat('NORBI', OBSERVERS, datetime.today()))

