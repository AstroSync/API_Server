from __future__ import annotations
import datetime
import json
import aiohttp
import os

# def request_device_condition(device_url=''):
#     if device_url == '':
#         raise ValueError(f'Incorrect device url: {device_url}')
#     response = requests.get('http://localhost:8082//get_device_condition')
#     result = response.content.decode('utf-8')
#     return result


async def connect_ground_stations():
    for gs in ground_stations:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{os.environ.get("ANTENNA_URL")}/rotator') as resp:
                result = await resp.text()
                print(f'result: {result}')
                if result is not None:
                    gs.connection_status = True
                    print(f'{gs.url} connected completely')
                


def get_station_url_by_name(name: str):
    return f'{os.environ.get("ANTENNA_URL")}'


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


class GroundStationModel:
    def __init__(self, url: str = '', position: str = ''):
        # data = request_device_condition(url)
        self.url: str = url
        self.observer: dict = {position: (54.842625, 83.095025, 170)}
        self.device: dict = {}
        self.connection_status: bool = False


ground_stations = [GroundStationModel(f'{os.environ.get("ANTENNA_URL")}', 'Новосибирск')]

