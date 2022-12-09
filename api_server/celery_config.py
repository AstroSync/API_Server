enable_utc = False
# result_extended = True
result_expires = 3600 * 24 * 30  # sec
mongodb_backend_settings = {
    'database': 'celery_db',
    'taskmeta_collection': 'tasks_collection',
}
# task_serializer = 'pickle'
# result_serializer = 'pickle'
accept_content = ['application/json', 'application/x-json']
task_serializer = 'json'
# accept_content = ['json']
result_serializer = 'json'
task_track_started = True
result_extended = True
timezone = 'Asia/Novosibirsk'