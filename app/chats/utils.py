from math import e
import redis

from django.conf import settings


redis_client = redis.Redis.from_url(settings.CACHES["default"]["LOCATION"])


def get_active_users_in_chat(chat_id):
    room_group_name = f"chat_{chat_id}"
    pattern = f"*{room_group_name}:active_users:*"
    print("checking for pattern", pattern)

    all_keys = set()
    cursor = 0

    while True:
        cursor, keys = redis_client.scan(match=pattern)
        {all_keys.add(key.decode().split(":")[-1]) for key in keys}
        if cursor == 0:
            break
    print("keys found", all_keys)
    return all_keys


def get_all_active_users():
    pattern = f"*last_seen_:*"
    print("checking for pattern", pattern)

    all_keys = set()
    cursor = 0

    while True:
        cursor, keys = redis_client.scan(match=pattern)
        {all_keys.add(key.decode().split(":")[-1]) for key in keys}
        if cursor == 0:
            break
    print("keys found", all_keys)
    return all_keys
