"""Film service: business logic for films."""

from typing import Optional
from uuid import UUID

from exceptions import ObjectNotFoundException
from models.films import Film
from repositories.films import AbstractFilmRepository
from utils import parse_sort_param


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
            field, order = parse_sort_param(sort)
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
