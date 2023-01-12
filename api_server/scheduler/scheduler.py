from datetime import datetime, timedelta
import time
from pymongo import MongoClient
from func_timeout import func_timeout, FunctionTimedOut, func_set_timeout
from apscheduler.events import EVENT_ALL, SchedulerEvent
from apscheduler.events import __all__ as apschedule_events_str
# from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler

from api_server.scheduler.mongo_store import MongoJobStore


class Scheduler:
    def __init__(self) -> None:
        self.scheduler: BaseScheduler = BackgroundScheduler(
            jobstores={'default': MongoJobStore(database='apscheduler',
                                                collection='jobs',
                                                client=MongoClient(host=f'mongodb://10.6.1.74',
                                                                   port=27017,
                                                                   username=f'root',
                                                                   password=f'rootpassword',
                                                                   authMechanism='DEFAULT',
                                                                   serverSelectionTimeoutMS=2000))
                       }
        )
        self.scheduler.add_listener(self.job_listener, mask=EVENT_ALL)
        self.scheduler.start()

    def job_listener(self, event: SchedulerEvent) -> None:
        apscheduler_events: dict[int, str] = dict(zip([1 << x for x in range(0, 17)], apschedule_events_str))
        event_str: str = apscheduler_events[event.code]
        # if len(event_str) != 0:
        #     event_str = event_str[0]
        print(f'{event_str}')


@func_set_timeout(3)
def test_job(start_time: datetime, duration: int, script_id: int) -> None:
    for i in range(5):
        time.sleep(1)
        print(i)

def session(start_time: datetime, duration: int, script_id: int = 32322134):
    try:
        test_job(start_time, duration, script_id)
    except FunctionTimedOut as err:
        print(err)
    return 'success'

if __name__ == '__main__':
    schedule = Scheduler()
    # schedule.scheduler._jobstores['default'].collection.delete_one({'_id': 'my_job'})
    schedule.scheduler.add_job(session, 'date', run_date=datetime.now() + timedelta(seconds=6), id='my_job',
                             kwargs={'start_time': datetime.now() + timedelta(seconds=6), 'duration': 10})
    schedule.scheduler.print_jobs()


    try:
        while True:
            time.sleep(3)
            schedule.scheduler.print_jobs()
    except (KeyboardInterrupt, SystemExit):
        schedule.scheduler.shutdown()
        print('Shutting down...')