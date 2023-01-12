from __future__ import annotations
from datetime import datetime, timedelta

import os
from threading import Thread
import time
from typing import Callable

from pytz import utc
from api_server.sessions_manager.mongodb_controller import MongoStore
from api_server.sessions_manager.session import Session

mongo_username: str = os.environ.get('MONGO_DB_USERNAME', 'root')
mongo_pass: str = os.environ.get('MONGO_DB_PASSWORD', 'rootpassword')
dbhost: str = os.environ.get('GS_ADDR', '10.6.1.74')

class Scheduler:
    def __init__(self, callback: Callable | None = None) -> None:
        self.jobstore: MongoStore = MongoStore(dbhost, mongo_username, mongo_pass, Session)
        self.prepare_time: int = 0
        self.misfire_grace_time: int = 5
        self.task_callback: Callable | None = callback
        self._thread: Thread
        self.__stop_flag: bool = True

    def start(self) -> None:
        if self.__stop_flag:
            self.__stop_flag = False
            self._thread = Thread(name='task_executer', target=self._tasks_execution_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self.__stop_flag = True
        self._thread.join()

    def set_callback(self, callback: Callable) -> None:
        self.task_callback = callback

    def get_next_task_time(self) -> str | None:
        next_task = self.jobstore.get_next(self.jobstore.schedule)
        if next_task is not None:
            next_task_sec: int = (next_task.start - datetime.now().astimezone(utc)).seconds
            return f'next task start at: {next_task.start.isoformat(" ", "seconds"), next_task_sec}'
        return None

    def _tasks_execution_loop(self) -> None:
        while not self.__stop_flag:
            try:
                time.sleep(1)
                next_session = self.jobstore.get_next(self.jobstore.schedule)
                next_origin = self.jobstore.get_next(self.jobstore.origin_ranges)
                now: datetime = datetime.now().astimezone(utc)
                if next_session is not None:
                    if now > next_session.start + timedelta(seconds=self.misfire_grace_time):
                        self.jobstore.add_missed(next_session)
                        self.jobstore.schedule.remove(next_session)
                        print('task missed')
                    elif now > next_session.start and callable(self.task_callback):
                        self.jobstore.schedule.remove(next_session)
                        print('start task')
                        self.task_callback()
                if next_origin is not None:
                    if now > next_origin.finish:
                        self.jobstore.simple_remove(next_origin)
            except RuntimeError as exc:
                print(exc)


if __name__ == '__main__':
    schedule = Scheduler()
    schedule.start()
    schedule.set_callback(lambda: print('start'))
    start_time: datetime = datetime.now().astimezone() + timedelta(seconds=5)
    s1: Session = Session(username='lolkek', start=start_time, duration_sec=10, priority=1)
    s2: Session = Session(username='gdfg', start=start_time + timedelta(seconds=2),  duration_sec=5, priority=2)
    schedule.jobstore.append(s1, s2)

    try:
        while True:
            time.sleep(1)
            print(schedule.get_next_task_time())
    except (KeyboardInterrupt, SystemExit):
        schedule.stop()
        print('Shutting down...')