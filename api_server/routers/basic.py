from __future__ import annotations
import hashlib
import json

import os
from datetime import date, datetime  #, timedelta, timezone
from tempfile import NamedTemporaryFile
from typing import Any, Union
from io import BytesIO, StringIO
from uuid import UUID

# from api_server.sessions_store.mongodb_controller import MongoStore
# from api_server.sessions_store.session import Session  #, uuid4
from fastapi import APIRouter, HTTPException, UploadFile  #, Depends , UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse  #, RedirectResponse,
# from fastapi_keycloak import OIDCUser  #, UsernamePassword
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from api_server.models.api import RegisterSessionModel, UserScriptMeta
#from api_server.database_api import db_add_user_script, db_register_new_session, get_all_sessions
# from api_server.hardware.naku_device_api import device
from api_server import celery_client
from api_server.models.db import UserScriptModel
from api_server.propagator.celestrak_api import get_sat_name_and_num
from api_server.propagator.propagate import OBSERVERS, SatellitePath, angle_points_for_linspace_time, get_sessions_for_sat
from api_server.sessions_store.scripts_store import script_store
# from api_server.keycloak import idp

router = APIRouter(tags=["Main"])
sat_names = get_sat_name_and_num(os.path.join(os.path.dirname(__file__), "../propagator/active.json"))


# @router.get("/user")
# async def root_user(user: OIDCUser = Depends(idp.get_current_user())):
#     return {"message": user.dict()}


@router.get("/app")
async def root():
    return {"message": "OK"}



@router.get("/satellites")
async def satellites():
    return sat_names

# @brouter.post("/register_new_session")
# async def register_new_session(data: RegisterSessionModel):
#     try:
#         print(f'type: {type(data)}, data: {data.json()}')
#         encoder = DateTimeEncoder()
#         async with aiohttp.ClientSession(json_serialize=encoder.encode) as session:
#             async with session.post(f"http://{os.environ.get('ANTENNA_URL')}/schedule/add_task",
#                                     json=data.dict(),
#                                     headers={'Content-Type': 'application/json'}) as resp:
#                 result = await resp.text()
#         print(result)
#         return result
#     except Exception as err:
#         return f'Error: {err}'
# @router.get("/check_station")
# async def check_station():
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(f"http://{os.environ.get('ANTENNA_URL')}/app") as resp:
#                 result = await resp.text()
#         print(result)
#         return result
#     except Exception as err:
#         return f'Error: {err}'
@router.get("/scripts/{user_id}", response_model=list[UserScriptMeta])
async def get_user_scripts_meta(user_id: UUID) -> list[UserScriptMeta]:
    scripts: list[UserScriptModel] = script_store.get_users_scripts(user_id)
    if len(scripts) > 0:
        scripts_meta: list[UserScriptMeta] = [UserScriptMeta.parse_obj(script) for script in scripts]
        return scripts_meta
    else:
        raise HTTPException(status_code=404, detail="Scripts not found.")


@router.get("/json/{file_name}")
async def get_json_file(file_name: str):
    try:
        with open(os.path.join(os.path.dirname(__file__), f"../geo_data/{file_name}"), encoding='utf-8') as file:
            return json.load(file)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="File was not found.") from exc


@router.post("/register_new_session")
async def register_new_session(request_body: RegisterSessionModel):
    #db_register_new_session(request_body.dict())
    print(request_body)
    return 'OK'


def pylint_check(path: str) -> tuple[int, int, str]:
    pylint_output: StringIO = StringIO()  # Custom open stream
    reporter: TextReporter = TextReporter(pylint_output)
    results: Run = Run(['--disable=missing-module-docstring', f'{path}'],
                  reporter=reporter, exit=False)
    errors: int = results.linter.stats.error
    fatal: int = results.linter.stats.fatal
    return errors, fatal, pylint_output.getvalue()


@router.post("/save_script")
async def save_script(user_id: UUID, user_script: UploadFile, script_name: str, description: str = ''):
    contents: bytes = await user_script.read()

    file_copy = NamedTemporaryFile(delete=False)
    file_copy.write(contents)  # copy the received file data into a new temp file.
    file_copy.seek(0)  # move to the beginning of the file

    errors, fatal, details = 0, 0, ''
    # errors, fatal, details = pylint_check(f'{file_copy.name}')
    if not errors:
        print('SCRIPT OK')
        now: datetime = datetime.now().astimezone()
        sha256: str = hashlib.sha256(contents).hexdigest()
        scriptModel=UserScriptModel(user_id=user_id, username='username', script_name=script_name, description=description,
                        content=contents, upload_date=now, last_edited_date=now, size=len(contents), sha256=sha256)
        script_store.save_script(scriptModel)
    else:
        print(f'{errors=}')
    file_copy.close()  # Remember to close any file instances before removing the temp file
    os.unlink(file_copy.name)  # unlink (remove) the file
    return {"result": details, "errors": errors, "fatal": fatal}


@router.post("/celery_check_script")
async def celery_check_script(user_id: UUID, user_script: UploadFile, script_name: str, description: str = ''):
    contents: bytes = await user_script.read()

    errors, fatal, details = celery_client.celery_pylint_check(contents).get()

    if not errors:
        print('SCRIPT OK')
        now: datetime = datetime.now().astimezone()
        sha256: str = hashlib.sha256(contents).hexdigest()
        scriptModel=UserScriptModel(user_id=user_id, username='username', script_name=script_name, description=description,
                        content=contents, upload_date=now, last_edited_date=now, size=len(contents), sha256=sha256)
        script_store.save_script(scriptModel)
    else:
        print(f'{errors=}')

    return {"result": details, "errors": errors, "fatal": fatal}


@router.get("/download_script/{script_id}", response_class=StreamingResponse)
async def download_script(script_id: UUID) -> StreamingResponse:
    model: UserScriptModel | None = script_store.get_script(script_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Script not found")
    return StreamingResponse(BytesIO(model.content), media_type='text/plain')

@router.delete("/delete_script")
async def delete_script(script_id: UUID) -> str:
    count: int = script_store.delete_script(script_id)
    print(f'{count=}')
    if count == 0:
        raise HTTPException(status_code=404, detail="Script not found")
    return 'Deleted'

@router.get("/sessions")
async def sessions(sat_name: str, start_date: Union[date, str] = datetime.utcnow().date(),
                   end_date: Union[date, str] = datetime.utcnow().date()):
    print(f'sat_name: {sat_name}, start_date: {start_date}, end_date: {end_date}')
    session_list: list[dict[str, Any]] = get_sessions_for_sat(sat_name=sat_name, observers=OBSERVERS,
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

@router.get("/celery_calculate_angles")
async def celery_calculate_angles(sat: str, t_1: datetime, t_2: datetime):
    return celery_client.celery_calculate_angles(sat, t_1, t_2).get()

@router.get("/{path:path}")
async def root_path(path: str):
    print(f'basic router catch path:{path}')
    return {"message": path}


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
