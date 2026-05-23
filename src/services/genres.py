"""Genre business logic service module."""

from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from core import config
from db.elastic import get_elastic
from exceptions import ObjectNotFoundException
from models.genres import Genre
from repositories.genres import AbstractGenreRepository, GenresRepository


class GenreService:
    """Service class for managing genre-related business logic."""

    def __init__(self, repository: AbstractGenreRepository):
        """Initialize service with specialized genre repository."""
        self.genre_repo = repository

    async def get_by_uuid(self, genre_uuid: UUID) -> Genre | None:
        """Get genre details by its unique identifier."""
        try:
            doc_source = await self.genre_repo.get_by_id(
                entity_id=str(genre_uuid)
            )
            return Genre(**doc_source)
        except ObjectNotFoundException:
            return None

    async def get_list(
        self,
        page_size: int,
        page_number: int,
        sort: str | None = None,
    ) -> list[Genre]:
        """Get sorted and paginated list of genres."""
        docs_sources = await self.genre_repo.get_sorted_genres(
            page_number=page_number,
            page_size=page_size,
            sort_str=sort,
        )
        return [Genre(**source) for source in docs_sources]


def get_genre_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    """Dependency provider for GenreService instantiation."""
    repository = GenresRepository(
        elastic_client=elastic, index=config.ELASTIC_GENRE_INDEX
    )
    return GenreService(repository)
