from pymongo import MongoClient, collection
import os


database_connection_status = False
pending_collection: collection = None
failed_collection: collection = None
completed_collection: collection = None

try:
    print('try to connect to db...')
    client = MongoClient(host=f'{os.environ.get("MONGO_DB_URL")}', 
                         port=eval(os.environ.get("MONGO_DB_PORT")), 
                         username=f'{os.environ.get("MONGO_DB_USERNAME")}',
                         password=f'{os.environ.get("MONGO_DB_PASSWORD")}', 
                         authMechanism='DEFAULT', serverSelectionTimeoutMS=2000)
    db = client['sessions']
    print("Connected to MongoDB")
    database_connection_status = True
    pending_collection = db['pending']
    failed_collection = db['failed']
    completed_collection = db['completed']
except Exception as e:
    print(f'Database connection failed: {e}')


def db_register_new_session(data):
    result = __check_same(data)
    if result is None:
        pending_collection.insert_one(data)
    else:
        print(f'Document {data} already exists.')


def __check_same(data):
    return pending_collection.find_one({'sat_name': data['sat_name'], 'session_list': data['session_list']})


def db_get_all_sessions():
    cursor = pending_collection.find({}, {'_id': False})
    return [session for session in cursor]

# def __find_data_in_db(collection: collection, data)


if __name__ == '__main__':
    print([x for x in pending_collection.find({'user_data.userId': 1}, {"_id": 0})])