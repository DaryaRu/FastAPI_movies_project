"""Utility functions for Elasticsearch indexes."""

import logging

from elasticsearch import AsyncElasticsearch, BadRequestError, NotFoundError
from elasticsearch.helpers import async_bulk

logger = logging.getLogger(__name__)


async def create_index(
    es_client: AsyncElasticsearch, index: str, schema: dict
) -> None:
    """Create ES index (if does not exist)."""
    try:
        await es_client.indices.create(
            index=index,
            settings=schema.get("settings"),
            mappings=schema.get("mappings"),
        )
    except BadRequestError:
        pass


async def delete_index(es_client: AsyncElasticsearch, index: str) -> None:
    """Delete ES index (skip if it does not exist)."""
    try:
        await es_client.indices.delete(index=index)
    except NotFoundError:
        pass


async def load_data(
    es_client: AsyncElasticsearch, index: str, data: list[dict]
) -> None:
    """Bulk-load documents into index and refresh."""
    updated, errors = await async_bulk(
        es_client,
        [{"_index": index, "_id": doc["id"], **doc} for doc in data],
        refresh=True,
    )
    if errors:
        logger.error(
            "Failed to index %d documents into '%s': %s",
            len(errors), index, errors,
        )
    else:
        logger.info(
            "Successfully indexed %d documents into '%s'", updated, index
        )
