

from datetime import datetime
import hashlib
from uuid import UUID
from fastapi import APIRouter, UploadFile
from api_server import celery_client
from api_server.models.db import SessionModel, UserScriptModel
from api_server.users.scripts_store import UserStore


router = APIRouter(prefix="/celery", tags=["Celery"])

@router.post("/check_script")
async def celery_check_script(user_id: UUID, user_script: UploadFile, script_name: str, description: str = ''):
    contents: bytes = await user_script.read()

    errors, fatal, details = celery_client.celery_pylint_check(contents).get()

    if not errors:
        print('SCRIPT OK')
        now: datetime = datetime.now().astimezone()
        sha256: str = hashlib.sha256(contents).hexdigest()
        scriptModel = UserScriptModel(user_id=user_id, username='username', script_name=script_name, description=description,
                        content=contents, upload_date=now, last_edited_date=now, size=len(contents), sha256=sha256)
        UserStore().save_script(scriptModel)
    else:
        print(f'{errors=}')

    return {"result": details, "errors": errors, "fatal": fatal}


@router.get("/calculate_angles")
async def celery_calculate_angles(sat: str, t_1: datetime, t_2: datetime):
    return celery_client.celery_calculate_angles(sat, t_1, t_2).get()


@router.get("/active_tasks")
async def celery_get_active_tasks():
    return celery_client.get_active_tasks()


@router.get("/scheduled_tasks")
async def celery_get_scheduled_tasks():
    tasks = celery_client.get_scheduled_tasks()
    return tasks

@router.get("/revoked_tasks")
async def celery_get_revoked_tasks():
    return celery_client.get_revoked_tasks()

@router.get("/scheduled_tasks/{user_id}", response_model=list[SessionModel])
async def celery_get_user_scheduled_tasks(user_id: UUID) -> list[SessionModel]:
    tasks = celery_client.get_scheduled_tasks()
    revoked_ids = celery_client.get_revoked_tasks()
    user_tasks: list[SessionModel]= [SessionModel.parse_obj(task['request']['kwargs']) for task in tasks['celery@NSU']
                                     if str(user_id) == task['request']['kwargs']['user_id']
                                     and task['request']['id'] not in revoked_ids['celery@NSU']]
    return user_tasks


@router.get("/reserved_tasks")
async def celery_get_reserved_tasks():
    return celery_client.get_reserved_tasks()
