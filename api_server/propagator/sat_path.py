from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
import numpy as np
from pytz import utc
from skyfield.api import load
from skyfield.units import Angle, Distance, AngleRate, Velocity
from skyfield.vectorlib import VectorSum
from skyfield.positionlib import Geocentric
from skyfield.sgp4lib import EarthSatellite
from skyfield.timelib import Time, Timescale

from api_server.propagator.propagate import OBSERVERS, download_tle


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

    def __getitem__(self, key):
        return (self.altitude[key], self.azimuth[key], self.t_points[key])

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
        self.altitude: np.ndarray = np.linspace(0.0, test_size, num=test_size)
        self.azimuth: np.ndarray = np.linspace(90.0, 90 + test_size, num=test_size)
        self.dist: np.ndarray = np.zeros(test_size)
        self.alt_rate: np.ndarray = np.ones(test_size)
        self.az_rate: np.ndarray = np.ones(test_size)
        self.dist_rate: np.ndarray = np.zeros(test_size)
        self.az_rotation_direction: int = 1
        self.t_points: list[datetime] = [datetime.now().astimezone(utc) + timedelta(seconds=6 + x) for x in range(test_size)]
        self.__index: int = 0

    def __getitem__(self, key) :
        return (self.altitude[key], self.azimuth[key], self.t_points[key])

    def __repr__(self) -> str:
        return f'Altitude deg from {self.altitude[0]:.2f} to {self.altitude[-1]:.2f}\n' \
               f'Azimuth deg from {self.azimuth[0]:.2f} to {self.azimuth[-1]:.2f}\n' \
               f'Distance km from {self.dist.min():.2f} to {self.dist.max():.2f}\n' \
               f'Altitude rate deg/s from {self.alt_rate.min():.2f} to {self.alt_rate.max():.2f}\n' \
               f'Azimuth rate deg/s from {self.az_rate.min():.2f} to {self.az_rate.max():.2f}\n' \
               f'Distance rate km/s from {self.dist_rate.min():.2f} to {self.dist_rate.max():.2f}\n' \
               f'Time points: from {self.t_points[0]} to {self.t_points[-1]}.\n' \
               f'Duration: {(self.t_points[-1] - self.t_points[0]).seconds} sec\n'

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
    satellite: EarthSatellite = download_tle(sat, local_tle)
    sat_position: VectorSum = (satellite - OBSERVERS[observer])
    topocentric: Geocentric = sat_position.at(time_points)  # type: ignore
    return SatellitePath(*topocentric.frame_latlon_and_rates(OBSERVERS[observer]),
                         time_points.utc_datetime())  # type: ignore

if __name__ == '__main__':
    start_time_: datetime = datetime.now(tz=timezone.utc)
    points: SatellitePath = angle_points_for_linspace_time('NORBI', 'NSU', start_time_,
                                                           start_time_ + timedelta(seconds=4), local_tle=False)
    print(points)
    for alt, az, t_point in points:
        print(alt, az, t_point)
