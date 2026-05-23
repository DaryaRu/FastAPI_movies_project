"""Film service: business logic for films."""

from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from core import config
from db.elastic import get_elastic
from exceptions import ObjectNotFoundException
from models.films import Film
from repositories.films import AbstractFilmRepository, FilmRepository


class FilmService:
    def __init__(self, repository: AbstractFilmRepository):
        """Initialize service with film repository."""
        self.repository = repository

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        """Return a film by id."""
        try:
            data = await self.repository.get_by_id(film_id)
        except ObjectNotFoundException:
            return None
        return Film(**data)

    async def get_list(
        self,
        sort: Optional[str],
        genre: Optional[UUID],
        page_number: int,
        page_size: int,
    ) -> list[Film]:
        """Return a paginated list of films (with sort and genre filter)."""
        query: dict | None = None
        if genre:
            query = {
                "nested": {
                    "path": "genres",
                    "query": {"term": {"genres.id": str(genre)}},
                }
            }

        sort_param: dict | None = None
        if sort:
            order = "desc" if sort.startswith("-") else "asc"
            field = sort.lstrip("-")
            sort_param = {field: {"order": order}}

        data = await self.repository.get_filtered(
            sort=sort_param,
            query=query,
            page_number=page_number,
            page_size=page_size,
        )
        return self._convert_to_films(data)

    async def search(
        self,
        query: str,
        page_number: int,
        page_size: int,
    ) -> list[Film]:
        """Search films by query string for title and description fields."""
        data = await self.repository.search_films(
            query_str=query,
            page_number=page_number,
            page_size=page_size,
        )
        return self._convert_to_films(data)

    def _convert_to_films(self, data: list[dict]) -> list[Film]:
        """Convert a list of raw dicts to Film objects."""
        return [Film(**item) for item in data]


def get_film_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    """FastAPI dependency that returns a FilmService instance."""
    repository = FilmRepository(elastic, index=config.ELASTIC_FILM_INDEX)
    return FilmService(repository)
