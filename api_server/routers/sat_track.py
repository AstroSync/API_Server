from __future__ import annotations
from datetime import date, datetime
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from api_server.propagator.celestrak_api import get_sat_name_and_num
from api_server.propagator.propagate import OBSERVERS, get_sessions_for_sat
from api_server.propagator.sat_path import SatellitePath, angle_points_for_linspace_time
from api_server.sessions_store.mongodb_controller import MongoStore
from api_server.sessions_store.session import Session
from api_server.sessions_store.time_range import TimeRange
# from api_server.keycloak import idp

router = APIRouter(tags=["Propagator"])


sat_names = get_sat_name_and_num(os.path.join(os.path.dirname(__file__), "../propagator/active.json"))


@router.get("/satellites")
async def satellites():
    return sat_names

def check_busy_sessions(new_sessions: list[dict]):
    store = MongoStore(os.environ.get('GS_ADDR', '10.13.13.6'), 'root', 'rootpassword', Session)
    schedule = [Session(**session) for session in store.get_schedule()]
    for session in new_sessions:
        for schedule_session in schedule:
            if TimeRange(**session) in schedule_session:
                session['status'] = 'Busy'
            else:
                session['status'] = 'Available'
    return new_sessions

@router.get("/sessions")
async def sessions(sat_name: str, start_date: date | str = datetime.utcnow().date(),
                   end_date: date | str = datetime.utcnow().date()):
    print(f'sat_name: {sat_name}, start_date: {start_date}, end_date: {end_date}')
    session_list, _ = get_sessions_for_sat(sat_name=sat_name, observers=OBSERVERS,
                                                              t_1=start_date, t_2=end_date, local_tle=True)
    print(session_list)
    session_list = check_busy_sessions(session_list)
    # schedule_list = MongoStore('10.6.1.74', 'root', 'rootpassword', Session).get_schedule()
    # for scheduled_session in schedule_list:
    #     for session in session_list:
    #         if session['']
    return JSONResponse(content=session_list)


@router.get("/calculate_angles")
async def calculate_angles(sat: str, t_1: datetime, t_2: datetime):
    path: SatellitePath = angle_points_for_linspace_time(sat, 'NSU', t_1, t_2)
    print(path.__repr__)
    return path.__repr__()

