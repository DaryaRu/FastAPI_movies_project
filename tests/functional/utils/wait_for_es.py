"""Script that waits for Elasticsearch service to start."""

import asyncio

from elasticsearch import AsyncElasticsearch

from functional.settings import test_settings


async def wait_for_es() -> None:
    """Ping ES in until it responds."""
    client = AsyncElasticsearch(
        hosts=[f"http://{test_settings.elastic_host}:{test_settings.elastic_port}"]
    )
    while True:
        if await client.ping():
            break
        await asyncio.sleep(1)
    await client.close()


if __name__ == "__main__":
    asyncio.run(wait_for_es())
