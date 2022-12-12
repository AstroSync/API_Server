from __future__ import annotations
from datetime import datetime, timedelta
from uuid import UUID  #, uuid4
from api_server.celery_client import celery_register_session, celery_register_session_test
from api_server.models.api import RegisterSessionModel
from api_server.sessions_store.session import Session
from api_server.sessions_store.mongodb_controller import MongoStore
from api_server.celery_client import celery_app


store = MongoStore('10.6.1.74', 'root', 'rootpassword', Session)


def register_sessions(new_sessions: list[RegisterSessionModel]):
    sessions: list[Session] = [Session(**session.dict()) for session in new_sessions]
    store.append(*sessions)
    async_result = [celery_register_session(session) for session in sessions]
    return async_result


def register_sessions_test(start_time: datetime = datetime.now() + timedelta(seconds=6), duration: int = 10):
    new_sessions = [RegisterSessionModel(user_id=UUID('388c01db-52a2-4192-9d6e-131958ea9e3a'),
                                        script_id=UUID('6e867ffa-264f-49a7-a58b-71de451f1c49'),
                                        username='kek',
                                        sat_name='NORBI',
                                        priority=1,
                                        start=start,
                                        duration_sec=duration) for start in [start_time, start_time + timedelta(seconds=duration + 80)]]
    sessions: list[Session] = [Session(**session.dict()) for session in new_sessions]
    store.append(*sessions)
    async_result = [celery_register_session_test(session) for session in sessions]
    return async_result


def cancel_sessions(sessions_id_list: list[UUID]) -> None:
    i = celery_app.control.inspect()
    tasks: list[dict[str, list[dict]]] = i.scheduled()
    # find id in tasks and mark as revoked


def set_session_priority(priority: int) -> None:
    pass

def set_session_script(session_id: UUID, script_id: UUID | None):
    pass

def remove_script(script_id: UUID) -> None:
    pass

def get_user_scripts(user_id: UUID) -> list:
    return []

def get_user_sessions(user_id: UUID) -> list:
    return []

def get_my_satellites(user_id: UUID) -> list:
    return []


if __name__ == '__main__':
    print(register_sessions_test(duration=10))