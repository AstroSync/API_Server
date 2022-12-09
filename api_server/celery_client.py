# from datetime import datetime
import time
from celery import group, signature
from api_server.sessions_store.session import Session
# from api_server.celery_tasks import radio_task, rotator_task_emulation
from celery import Celery
from api_server import celery_config

print('Created celery app')

host = '10.6.1.74' # 'localhost'
celery_app: Celery = Celery('ground_station', broker=f'amqp://guest:guest@{host}:5672//',
                            # backend="redis://localhost:6379/0",
                            # backend='mongodb://root:rootpassword@astrosync.ru:27017/?authMechanism=DEFAULT',
                            backend=f'mongodb://root:rootpassword@{host}:27017/?authMechanism=DEFAULT',
                            # backend = 'db+postgresql+psycopg2://testkeycloakuser:testkeycloakpassword@postgres/testkeycloakdb',
                            include=['ground_station.celery_tasks'])
celery_app.config_from_object(celery_config)


def celery_register_session(model: Session):
    soft_time_limit: float = model.duration_sec + 3.0
    time_limit: float = soft_time_limit + 8.0

    radio = signature('ground_station.celery_tasks.radio_task', args=(),
                                                   kwargs=model.__dict__,
                                                   eta=model.start,
                                                   soft_time_limit=soft_time_limit,
                                                   time_limit=time_limit)
    rotator = signature('ground_station.celery_tasks.rotator_task', args=(),
                                                   kwargs=model.__dict__,
                                                   eta=model.start,
                                                   soft_time_limit=soft_time_limit,
                                                   time_limit=time_limit)

    group_task: group = group(radio, rotator)
    return group_task.apply_async()

def celery_register_session_test(model: Session):
    soft_time_limit: float = model.duration_sec + 3.0
    time_limit: float = soft_time_limit + 8.0

    radio = signature('ground_station.celery_tasks.radio_task', args=(),
                                                   kwargs=model.__dict__,
                                                   eta=model.start,
                                                   soft_time_limit=soft_time_limit,
                                                   time_limit=time_limit)
    rotator = signature('ground_station.celery_tasks.rotator_task_emulation', args=(),
                                                   kwargs=model.__dict__,
                                                   eta=model.start,
                                                   soft_time_limit=soft_time_limit,
                                                   time_limit=time_limit)

    group_task: group = group(radio, rotator)
    return group_task.apply_async()

def connect():
    return celery_app.send_task('ground_station.celery_tasks.connect', ignore_result=True).get()

def get_position():
    return celery_app.send_task('ground_station.celery_tasks.get_angle').get()

def set_angle(az: float, el: float):
    return celery_app.send_task('ground_station.celery_tasks.set_angle', args=(az, el)).get()

def radio_send(msg: list[int] | bytes):
    return celery_app.send_task('ground_station.celery_tasks.radio_send', args=(msg)).get()

def shutdown_worker():
    celery_app.control.broadcast('shutdown', destination=['NSU'])



if __name__ == '__main__':
    # data = Session(start=datetime.now(), username='Test User', result='0xAB 0x21 0xCD 0x78 0x01')
    # print(data.__dict__)
    # print(register_session(data).get())
    # print(connect())
    # print(Model.parse_obj(get_position().get()))
    print(set_angle(70, 0))
    time.sleep(2)
    print(get_position())
    # print(celery_app.control.purge())
    # print(celery_app.control.broadcast('purge', destination=['NSU']))
    # while True:

    # celery_app.control.revoke('3343b68e-eae1-408a-a890-5183fb56140d')
# az67 el:49

#az 120api = 127rot; el 51api = 90rot