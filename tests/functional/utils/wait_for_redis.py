import time

import redis

from settings import test_settings


if __name__ == '__main__':
    redis_client = redis.Redis(
        host=test_settings.redis_host,
        port=test_settings.redis_port,
    )

    while True:
        try:
            if redis_client.ping():
                break
        except redis.exceptions.ConnectionError:
            pass

        time.sleep(1)
