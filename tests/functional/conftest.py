"""Fixtures for functional tests."""

import httpx
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis

from functional.settings import test_settings
from functional.utils.helpers import create_index, delete_index, load_data


@pytest_asyncio.fixture(scope="session")
async def es_client():
    """Session-scoped Elasticsearch async client."""
    client = AsyncElasticsearch(
        hosts=[f"http://{test_settings.elastic_host}:{test_settings.elastic_port}"]
    )
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="session")
async def redis_client():
    """Session-scoped Redis async client."""
    client = Redis(host=test_settings.redis_host, port=test_settings.redis_port)
    yield client
    await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def flush_cache(redis_client: Redis):
    """Flushe Redis cache before each test."""
    await redis_client.flushdb()


@pytest_asyncio.fixture
async def http_client():
    """Function-scoped httpx async client."""
    limits = httpx.Limits(max_keepalive_connections=0)
    async with httpx.AsyncClient(
        base_url=test_settings.api_url, limits=limits
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def es_write_data(es_client: AsyncElasticsearch):
    """Fixture for loading test data into Elasticsearch."""
    created_indices = []

    async def inner(index: str, schema: dict, data: list[dict]) -> None:
        await create_index(es_client, index, schema)
        await load_data(es_client, index, data)
        created_indices.append(index)

    yield inner

    for index in created_indices:
        await delete_index(es_client, index)
