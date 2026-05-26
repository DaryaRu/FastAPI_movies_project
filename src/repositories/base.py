"""Base Elasticsearch repository."""

from abc import ABC

from elasticsearch import AsyncElasticsearch, BadRequestError, NotFoundError

from exceptions import ObjectNotFoundException


class BaseElasticRepository(ABC):
    """Base repository for Elasticsearch operations."""

    def __init__(self, elastic_client: AsyncElasticsearch, index: str):
        """Initialize with an Elasticsearch client and index name."""
        self.elastic_client = elastic_client
        self.index = index

    async def get_by_id(
        self,
        entity_id: str,
        source: list[str] | None = None,
    ) -> dict:
        """Fetch a single document by id."""
        try:
            doc = await self.elastic_client.get(
                index=self.index,
                id=entity_id,
                source_includes=source,
            )
        except NotFoundError as ex:
            raise ObjectNotFoundException from ex
        return doc["_source"]

    async def get_filtered(
        self,
        page_size: int | None = None,
        page_number: int | None = None,
        query: dict | None = None,
        sort: dict | None = None,
        source: list[str] | None = None,
    ) -> list[dict]:
        """Search documents with optional query, sort, and pagination."""
        body = {
            "query": query or {"match_all": {}},
        }
        if source:
            body["_source"] = source
        if page_size and page_number:
            body["from"] = (page_number - 1) * page_size
            body["size"] = page_size

        if sort:
            body["sort"] = [sort]

        try:
            result = await self.elastic_client.search(
                index=self.index,
                body=body,
            )
        except (BadRequestError, NotFoundError):
            return []

        return [hit["_source"] for hit in result["hits"]["hits"]]
