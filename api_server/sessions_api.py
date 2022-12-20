from __future__ import annotations
from datetime import datetime, timedelta
from multiprocessing.pool import ApplyResult
import os
from uuid import UUID

from pytz import utc  #, uuid4
from api_server.celery_client import celery_register_session, celery_register_session_test
from api_server.models.api import RegisterSessionModel
from api_server.sessions_store.session import Session
from api_server.sessions_store.mongodb_controller import MongoStore
# from api_server.celery_client import celery_app

host: str = os.environ.get('GS_ADDR', '10.6.1.74')
store = MongoStore(host, 'root', 'rootpassword', Session)


def register_sessions(new_sessions: list[RegisterSessionModel]):
    sessions: list[Session] = [Session(**session.dict()) for session in new_sessions]
    store.append(*sessions)
    # регистрировать только после анализа расписания
    async_results = [celery_register_session(session) for session in sessions]
    return [result.forget() for result in async_results] # type: ignore


def register_sessions_test(data_list: list[tuple[datetime, int]] | None = None):
    if data_list is None:
        data_list = [(datetime.now(utc) + timedelta(seconds=6), 10)]
    new_sessions: list = [RegisterSessionModel(user_id=UUID('19381611-6cc5-4635-bb05-2d71ae341fcb'),
                                               script_id=UUID('cee1a05d-fe18-4334-b40c-146eb7dc92b9'),
                                               username='kek',
                                               sat_name='NORBI',
                                               priority=1,
                                               start=data[0],
                                               duration_sec=data[1]) for data in data_list]
    sessions: list[Session] = [Session(**session.dict()) for session in new_sessions]

    # store.append(*sessions)
    async_results: list[ApplyResult] = [celery_register_session_test(session) for session in sessions]
    return [result.forget() for result in async_results]  # type: ignore


# def cancel_sessions(sessions_id_list: list[UUID]) -> None:
#     i = celery_app.control.inspect()
#     tasks: list[dict[str, list[dict]]] = i.scheduled()
#     # find id in tasks and mark as revoked


# def set_session_priority(priority: int) -> None:
#     pass

# def set_session_script(session_id: UUID, script_id: UUID | None):
#     pass

# def remove_script(script_id: UUID) -> None:
#     pass

# def get_user_scripts(user_id: UUID) -> list:
#     return []

# def get_user_sessions(user_id: UUID) -> list:
#     return []

# def get_my_satellites(user_id: UUID) -> list:
#     return []


if __name__ == '__main__':
    print(register_sessions_test())