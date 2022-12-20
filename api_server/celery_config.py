enable_utc = True
result_extended = True
result_expires = 3600  # sec
# mongodb_backend_settings = {
#     'database': 'celery_db',
#     'taskmeta_collection': 'tasks_collection',
# }
# task_serializer = 'pickle'
# result_serializer = 'pickle'
accept_content = ['application/json', 'application/x-json']
task_serializer = 'json'
# accept_content = ['json']
result_serializer = 'json'
task_track_started = True
# result_extended = True
# ignore_result = True
# timezone = 'Asia/Novosibirsk'
visibility_timeout = 60000000
result_backend_transport_options = broker_transport_options = { 'visibility_timeout': 60000000 }
