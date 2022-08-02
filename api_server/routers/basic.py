from __future__ import annotations
import datetime
import json
import os
from typing import Union
from datetime import date
import aiohttp
from fastapi import APIRouter, HTTPException
from api_server.database_api import db_register_new_session, db_get_all_sessions
from api_server.gs_device_model import ground_stations, GroundStationModel
from api_server.models import RegisterSessionModel
from api_server.propagator.celestrak_api import get_sat_name_and_num
from api_server.propagator.propagate import get_sessions_for_sat


basic_router = APIRouter(tags=["Main"])
sat_names = get_sat_name_and_num(os.path.join(os.path.dirname(__file__), "../propagator/active.json"))


@basic_router.get("/app")
async def root():
    return {"message": "OK"}


@basic_router.get("/ground_stations")
async def get_ground_stations() -> list[GroundStationModel]:
    return ground_stations


@basic_router.get("/satellites")
async def satellites():
    return sat_names


class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()

        return super(DateTimeEncoder, self).default(obj)


@basic_router.post("/register_new_session")
async def register_new_session(data: RegisterSessionModel):
    try:
        print(f'type: {type(data)}, data: {data.json()}')
        encoder = DateTimeEncoder()
        async with aiohttp.ClientSession(json_serialize=encoder.encode) as session:
            async with session.post(f"http://{os.environ.get('ANTENNA_URL')}/schedule/add_task", 
                                    json=data.dict(),
                                    headers={'Content-Type': 'application/json'}) as resp:
                result = await resp.text()
        print(result)
        return result
    except Exception as err:
        return f'Error: {err}'


@basic_router.get("/check_station")
async def check_station():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{os.environ.get('ANTENNA_URL')}/app") as resp:
                result = await resp.text()
        print(result)
        return result
    except Exception as err:
        return f'Error: {err}'


@basic_router.get("/pending_sessions")
async def get_pending_sessions():
    sessions: list[dict] = db_get_all_sessions()
    # print(sessions)
    return sessions


@basic_router.get("/sessions")
async def sessions(sat_name: str, start_date: Union[date, str] = date.today(),
                   end_date: Union[date, str] = date.today()):
    print(f'sat_name: {sat_name}, start_date: {start_date}, end_date: {end_date}')
    session_list = get_sessions_for_sat(sat_name=sat_name, t1=start_date, t2=end_date)
    if session_list == ValueError:
        raise HTTPException(status_code=404, detail="Satellite name was not found.")
    return session_list


@basic_router.get("/json/{file_name}")
async def get_json_file(file_name: str):
    try:
        with open(os.path.join(os.path.dirname(__file__), f"../geo_data/{file_name}")) as file:
            return json.load(file)
    except Exception:
        raise HTTPException(status_code=404, detail="File was not found.")
    

@basic_router.get("/{path:path}")
async def root(path: str):
    print(f'catch {path}')
    return {"message": path}


# user_script = """
# import time
# print('Running user script')
# for i in range(50):
#     time.sleep(0.1
#     print(f'some processing {i}')
# print('User script completed')
# """
# if __name__ == "__main__":
#     f = lambda: exec(compile(user_script, "<string>", "exec"))
#     f()
# frontend_server = True
#
#
# @router.get("/", response_class=HTMLResponse)
# @router.get("/{path:path}")
# async def catch_all(request: Request, path: str):
#     print(f'path_name: {path}')
#     if frontend_server:
#         if path == '':
#             return HTMLResponse(requests.get(f'http://localhost:8000/{path}').content)
#         else:
#             return HTMLResponse(requests.get(f'http://localhost:8000/{path}').content)
# return FileResponse(f'{dist_path}/{path.lstrip("/")}')
