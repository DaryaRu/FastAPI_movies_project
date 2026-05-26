"""Film service: business logic for films."""

from typing import Optional
from uuid import UUID

from exceptions import ObjectNotFoundException
from models.films import Film
from repositories.films import AbstractFilmRepository


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
        data = await self.repository.get_list(
            sort=sort,
            genre=genre,
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
