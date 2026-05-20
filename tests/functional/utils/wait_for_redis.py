"""Script that waits for Redis service to start."""

import asyncio

from redis.asyncio import Redis

from functional.settings import test_settings


async def wait_for_redis() -> None:
    """Ping Redis until it responds."""
    client = Redis(
        host=test_settings.redis_host,
        port=test_settings.redis_port,
    )
    while True:
        if await client.ping():
            break
        await asyncio.sleep(1)
    await client.close()


if __name__ == "__main__":
    asyncio.run(wait_for_redis())
