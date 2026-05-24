import asyncio
from typing import Awaitable, Callable

import aiohttp
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from redis.asyncio import Redis

from settings import test_settings

pytest_plugins = [
    'fixtures.persons'
]


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(loop_scope="function")
async def http_client():
    """Function-scoped aiohttp client session."""
    async with aiohttp.ClientSession(
        base_url=test_settings.service_url
    ) as session:
        yield session


@pytest_asyncio.fixture(name='es_client', scope='session')
async def es_client() -> AsyncElasticsearch:
    es_client = AsyncElasticsearch(hosts=test_settings.es_host, verify_certs=False)
    yield es_client
    await es_client.close()
    
    
@pytest_asyncio.fixture(name='es_write_data', scope='session')
def es_write_data(es_client: AsyncElasticsearch) -> Callable[[list[dict], str, dict, dict], Awaitable[None]]:
    async def inner(data: list[dict], index: str, mapping: dict, settings: dict) -> None:
        if await es_client.indices.exists(index=index):
            await es_client.indices.delete(index=index)
        await es_client.indices.create(index=index, mappings=mapping, settings=settings)

        _, errors = await async_bulk(client=es_client, actions=data)
        print(f'Errors: {errors}')
        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')
        await es_client.indices.refresh(index=index)

    return inner
    
    
@pytest_asyncio.fixture()
async def redis_client():
    client = Redis(
        host=test_settings.redis_host,
        port=test_settings.redis_port,
        decode_responses=True,
    )
    yield client
    await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def flush_cache(redis_client: Redis):
    await redis_client.flushdb()
