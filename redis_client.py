import redis

r = redis.Redis(
  host='redis-18108.c299.asia-northeast1-1.gce.cloud.redislabs.com',
  port=18108,
  username='default',
  password='WvxzTaBH7S13YqrAjrMIPXEW8iIHUQCQ',
)

user_data_decoded = {key.decode('utf-8'): value.decode('utf-8') for key, value in r.hgetall('user:1').items()}
print(user_data_decoded)