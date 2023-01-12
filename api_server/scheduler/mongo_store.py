from __future__ import annotations
from datetime import datetime
import json
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.job import Job
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.triggers.date import DateTrigger
from apscheduler.util import datetime_to_utc_timestamp
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError


def encoder(obj) -> str | dict:
    if isinstance(obj, datetime):
        return obj.isoformat(' ', 'seconds')
        # return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, DateTrigger):
        return str(obj)
    print(type(obj), obj)
    return obj.__dict__

def decoder(obj):
    # if isinstance(obj, dict):
    #     if 'azimuth' in obj:
    #         return RotatorModel(**obj)
    return obj

def my_dumps(obj):
    return json.loads(json.dumps(obj, default=encoder))

def my_loads(obj) -> dict:
    return json.loads(str(obj).replace('\'', '\"'), object_hook=decoder)

class MongoJobStore(MongoDBJobStore):
    def __init__(self, database='apscheduler', collection='jobs', client=None, **connect_args):
        super().__init__(database, collection, client, **connect_args)



    def add_job(self, job: Job):
        try:
            j = {
                '_id': job.id,
                'next_run_time': datetime_to_utc_timestamp(job.next_run_time),
                'job_state': my_dumps(job.__getstate__())
            }
            result = self.collection.insert_one(j)
            print(result)
        except DuplicateKeyError as exc:
            raise ConflictingIdError(job.id) from exc

    def update_job(self, job: Job):
        changes = {
            'next_run_time': datetime_to_utc_timestamp(job.next_run_time),
            'job_state': my_dumps(job.__getstate__())
        }
        result = self.collection.update_one({'_id': job.id}, {'$set': changes})
        if result and result.matched_count == 0:
            raise JobLookupError(job.id)

    # def lookup_job(self, job_id):
    #     document = self.collection.find_one(job_id, ['job_state'])
    #     return self._reconstitute_job(document['job_state']) if document else None

    def _reconstitute_job(self, job_state: dict):
        job: Job = Job.__new__(Job)
        job.__setstate__(job_state)
        job.next_run_time = datetime.fromisoformat(job.next_run_time)
        job.trigger = DateTrigger(job.next_run_time)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job

    # def _get_jobs(self, conditions):
    #     jobs: list[Job] = []
    #     failed_job_ids: list[Job] = []
    #     for document in self.collection.find(conditions, ['_id', 'job_state'],
    #                                          sort=[('next_run_time', ASCENDING)]):
    #         try:
    #             jobs.append(self._reconstitute_job(document['job_state']))
    #         except BaseException:
    #             self._logger.exception('Unable to restore job "%s" -- removing it',
    #                                    document['_id'])
    #             failed_job_ids.append(document['_id'])