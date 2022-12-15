from datetime import datetime, timedelta
from fastapi import APIRouter

from api_server.models.api import RegisterSessionModel
from api_server import sessions_api
# from api_server.db_models import RegisterSessionModel


router = APIRouter(prefix="/schedule", tags=["Schedule"])


@router.get('/')
async def get_schedule():
    return ''


@router.post('/register_sessions')
async def register_sessions(new_sessions: list[RegisterSessionModel]):
    sessions_api.register_sessions(new_sessions)
    return {"message": "OK"}


@router.post('/register_sessions_test')
async def register_sessions_test(data_list: list[tuple[datetime, int]] = [(datetime.now() + timedelta(seconds=6), 10)]):
    sessions_api.register_sessions_test(data_list)
    return {"message": "OK"}

# @router.get('/get_pending_tasks')
# async def get_pending_tasks(user_id: int):
#     return list(pending_collection.find({'user_data.userId': user_id}, {"_id": 0}))


# @router.get('/get_completed_tasks')
# async def get_completed_tasks(user_id: int):
#     return list(completed_collection.find({'user_data.userId': user_id}, {"_id": 0}))


# @router.get('/get_failed_tasks')
# async def get_failed_tasks(user_id: int):
#     return list(failed_collection.find({'user_data.userId': user_id}, {"_id": 0}))

