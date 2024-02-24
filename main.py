# import json
# import redis

# r = redis.Redis(host='redis-18108.c299.asia-northeast1-1.gce.cloud.redislabs.com', port=18108, db=0, username='default',password='WvxzTaBH7S13YqrAjrMIPXEW8iIHUQCQ',decode_responses=True)


# with open('./user.json', 'r') as file:
#     user_data = json.load(file)

# for user in user_data:
#     user_id = user['id']
#     r.hset(f'user:{user_id}', mapping=user)

# import json
# import redis

# r = redis.Redis(host='redis-18108.c299.asia-northeast1-1.gce.cloud.redislabs.com', port=18108, db=0, username='default',password='WvxzTaBH7S13YqrAjrMIPXEW8iIHUQCQ',decode_responses=True)
# with open('./pictures.json', 'r') as file:
#     pictures_data = json.load(file)

# for picture_id, picture_info in pictures_data.items():
#     r.hset(f'picture:{picture_id}', mapping=picture_info)
