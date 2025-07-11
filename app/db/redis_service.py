import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

chart = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
metric = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=2, decode_responses=True)
kiwoom_token = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=9, decode_responses=True)


def get_redis(db):
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=db, decode_responses=True)
    except redis.RedisError as e:
        raise ConnectionError(f"Redis 연결 실패: {str(e)}")

# 캐시 저장 헬퍼
def set_cache(client, key, value, ttl=3600):
    try:
        client.setex(key, ttl, value)
    except redis.RedisError as e:
        print(f"Redis 저장 실패: {e}")

# 캐시 조회 헬퍼
def get_cache(client, key):
    try:
        return client.get(key)
    except redis.RedisError as e:
        print(f"Redis 조회 실패: {e}")
        return None