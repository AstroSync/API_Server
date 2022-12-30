from __future__ import annotations
from datetime import date, datetime
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from api_server.propagator.celestrak_api import get_sat_name_and_num
from api_server.propagator.propagate import OBSERVERS, SatellitePath, \
                                            angle_points_for_linspace_time, get_sessions_for_sat
# from api_server.keycloak import idp

router = APIRouter(tags=["Propagator"])


sat_names = get_sat_name_and_num(os.path.join(os.path.dirname(__file__), "../propagator/active.json"))


@router.get("/satellites")
async def satellites():
    return sat_names

@router.get("/sessions")
async def sessions(sat_name: str, start_date: date | str = datetime.utcnow().date(),
                   end_date: date | str = datetime.utcnow().date()):
    print(f'sat_name: {sat_name}, start_date: {start_date}, end_date: {end_date}')
    session_list, _ = get_sessions_for_sat(sat_name=sat_name, observers=OBSERVERS,
                                                              t_1=start_date, t_2=end_date, local_tle=True)
    print(session_list)
    # schedule_list = MongoStore('10.6.1.74', 'root', 'rootpassword', Session).get_schedule()
    # for scheduled_session in schedule_list:
    #     for session in session_list:
    #         if session['']
    if session_list == ValueError:
        raise HTTPException(status_code=404, detail="Satellite name was not found.")
    return JSONResponse(content=session_list)


@router.get("/calculate_angles")
async def calculate_angles(sat: str, t_1: datetime, t_2: datetime):
    path: SatellitePath = angle_points_for_linspace_time(sat, 'NSU', t_1, t_2)
    print(path.__repr__)
    return path.__repr__()
