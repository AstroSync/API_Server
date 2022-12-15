# from datetime import datetime
from __future__ import annotations
from datetime import datetime
from multiprocessing.pool import AsyncResult
# import sys
import time
from celery import Celery  #, group, signature
from api_server.sessions_store.session import Session
from api_server import celery_config
# from api_server.celery_tasks import radio_task, rotator_task_emulation

print('Created celery app')

host: str = '10.6.1.74' # 'localhost'
# if sys.platform.startswith('win'):
celery_app: Celery = Celery('ground_station',
                            broker=f'redis://{host}:6379/0',
                            #  broker=f'amqp://guest:guest@{host}:5672//',
                            backend=f"redis://{host}:6379/0",
                            # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
                            # backend=f'mongodb://root:rootpassword@{host}:27017/?authMechanism=DEFAULT',
                            # backend = 'db+postgresql+psycopg2://testkeycloakuser:testkeycloakpassword@postgres/testkeycloakdb',
                            include=['ground_station.celery_tasks'])
# else:  # docker
#     celery_app = Celery('celery_worker', broker='amqp://guest:guest@localhost:5672//',
#                                 # backend="redis://redis:6379/0",
#                                 # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
#                                 backend='mongodb://root:rootpassword@localhost:27017/?authMechanism=DEFAULT',
#                                 # backend = 'db+postgresql+psycopg2://testkeycloakuser:testkeycloakpassword@postgres/testkeycloakdb',
#                                 include=['ground_station.celery_tasks'])
celery_app.config_from_object(celery_config)


def celery_register_session(model: Session) -> AsyncResult:
    soft_time_limit: float = model.duration_sec + 3.0
    time_limit: float = soft_time_limit + 8.0

    # radio = signature('ground_station.celery_tasks.radio_task', args=(),
    #                                                kwargs=model.__dict__,
    #                                                eta=model.start,
    #                                                soft_time_limit=soft_time_limit,
    #                                                time_limit=time_limit)
    # rotator = signature('ground_station.celery_tasks.rotator_task', args=(),
    #                                                kwargs=model.__dict__,
    #                                                eta=model.start,
    #                                                soft_time_limit=soft_time_limit,
    #                                                time_limit=time_limit)

    # group_task: group = group(radio, rotator)
    return celery_app.send_task('ground_station.celery_tasks.radio_task', kwargs=model.__dict__,
                                                                          eta=model.start,
                                                                          soft_time_limit=soft_time_limit,
                                                                          time_limit=time_limit)

def celery_register_session_test(model: Session) -> AsyncResult:
    soft_time_limit: float = model.duration_sec + 3.0
    time_limit: float = soft_time_limit + 10.0

    # radio = signature('ground_station.celery_tasks.radio_task', args=(),
    #                                                kwargs=model.__dict__,
    #                                                eta=model.start,
    #                                                soft_time_limit=soft_time_limit,
    #                                                time_limit=time_limit)
    # rotator = signature('ground_station.celery_tasks.rotator_task_emulation', args=(),
    #                                                kwargs=model.__dict__,
    #                                                eta=model.start,
    #                                                soft_time_limit=soft_time_limit,
    #                                                time_limit=time_limit)

    # group_task: group = group(radio, rotator)
    # return group_task.apply_async()
    kwargs = model.__dict__
    kwargs.update({'test': True})
    return celery_app.send_task('ground_station.celery_tasks.radio_task', kwargs=kwargs,
                                                                          eta=model.start,
                                                                          soft_time_limit=soft_time_limit,
                                                                          time_limit=time_limit)

def celery_calculate_angles(sat: str, t_1: datetime, t_2: datetime) -> AsyncResult:
    return celery_app.send_task('ground_station.celery_tasks.calculate_angles', args=(sat, t_1, t_2))

def connect() -> AsyncResult:
    return celery_app.send_task('ground_station.celery_tasks.connect_naku')

def disconnect():
    return celery_app.send_task('ground_station.celery_tasks.disconnect_naku')

def get_position() -> AsyncResult:
    return celery_app.send_task('ground_station.celery_tasks.get_angle')

def get_config() -> AsyncResult:
    return celery_app.send_task('ground_station.celery_tasks.get_config')

def set_speed(az_speed: float, el_speed: float) -> AsyncResult:
    return celery_app.send_task('ground_station.celery_tasks.set_speed', args=(az_speed, el_speed))

def set_angle(az: float, el: float) -> AsyncResult:
    return celery_app.send_task('ground_station.celery_tasks.set_angle', args=(az, el))

def radio_send(msg: list[int] | bytes) -> AsyncResult:
    return celery_app.send_task('ground_station.celery_tasks.radio_send', args=(msg))

def celery_pylint_check(content: bytes) -> AsyncResult:
    return celery_app.send_task('ground_station.celery_tasks.pylint_check', args=(content))

def shutdown_worker():
    celery_app.control.broadcast('shutdown', destination=['NSU'])



if __name__ == '__main__':
    # data = Session(start=datetime.now(), username='Test User', result='0xAB 0x21 0xCD 0x78 0x01')
    # print(data.__dict__)
    # print(register_session(data).get())
    # print(connect())
    # print(Model.parse_obj(get_position().get()))
    print(set_angle(70, 0).get())
    time.sleep(2)
    print(get_position().get())
    # print(celery_app.control.purge())
    # print(celery_app.control.broadcast('purge', destination=['NSU']))
    # while True:

    # celery_app.control.revoke('3343b68e-eae1-408a-a890-5183fb56140d')
# az67 el:49

#az 120api = 127rot; el 51api = 90rot