"""Person business logic service module."""

from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from core import config
from db.elastic import get_elastic
from exceptions import ObjectNotFoundException
from models.persons import Person as PersonModel
from repositories.films import AbstractFilmRepository, FilmRepository
from repositories.persons import AbstractPersonRepository, PersonsRepository
from schemas.film_shorts import FilmShortResponse as FilmShort


class PersonService:
    """Service class for managing person-related business logic."""

    def __init__(
        self,
        person_repo: AbstractPersonRepository,
        movie_repo: AbstractFilmRepository,
    ):
        """Initialize service with specialized repositories."""
        self.person_repo = person_repo
        self.movie_repo = movie_repo

    async def get_by_uuid(self, person_uuid: UUID) -> PersonModel | None:
        """Get person details by their unique identifier."""
        try:
            doc_source = await self.person_repo.get_by_id(str(person_uuid))
            return PersonModel(**doc_source)
        except ObjectNotFoundException:
            return None

    async def get_list(
        self,
        page_size: int,
        page_number: int,
        query: str | None = None,
    ) -> list[PersonModel]:
        """Get a full-text searched or paginated list of persons."""
        if query:
            docs_sources = await self.person_repo.search_persons(
                query_str=query, page_number=page_number, page_size=page_size
            )
        else:
            docs_sources = await self.person_repo.get_filtered(
                page_size=page_size,
                page_number=page_number,
                query={"match_all": {}},
            )
        return [PersonModel(**source) for source in docs_sources]

    async def get_person_films(
        self,
        person_uuid: UUID,
        page_size: int,
        page_number: int,
    ) -> list[FilmShort] | None:
        """
        Get all films associated with a specific person via nested queries.
        """
        person = await self.get_by_uuid(person_uuid)
        if not person:
            return None

        movie_query = {
            "bool": {
                "should": [
                    {
                        "nested": {
                            "path": "actors",
                            "query": {"term": {"actors.id": str(person_uuid)}},
                        }
                    },
                    {
                        "nested": {
                            "path": "writers",
                            "query": {
                                "term": {"writers.id": str(person_uuid)}
                            },
                        }
                    },
                    {
                        "nested": {
                            "path": "directors",
                            "query": {
                                "term": {"directors.id": str(person_uuid)}
                            },
                        }
                    },
                ]
            }
        }

        movies_sources = await self.movie_repo.get_filtered(
            page_size=page_size, page_number=page_number, query=movie_query
        )

        result = []
        for source in movies_sources:
            actual_id = source.get("id") or source.get("uuid")
            if actual_id:
                source["id"] = actual_id
                source["uuid"] = actual_id
            result.append(FilmShort(**source))
        return result


def get_person_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    """Dependency provider for PersonService instantiation."""
    person_repo = PersonsRepository(
        elastic_client=elastic, index=config.ELASTIC_PERSON_INDEX
    )
    movie_repo = FilmRepository(
        elastic_client=elastic, index=config.ELASTIC_FILM_INDEX
    )
    return PersonService(person_repo=person_repo, movie_repo=movie_repo)
