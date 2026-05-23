"""Genres repository."""

from abc import abstractmethod

from repositories.base import BaseElasticRepository


class AbstractGenreRepository(BaseElasticRepository):
    """Abstract contract for genre repositories."""

    @abstractmethod
    async def get_sorted_genres(
        self,
        page_number: int,
        page_size: int,
        sort_str: str | None,
    ) -> list[dict]: ...


class GenresRepository(AbstractGenreRepository):
    """Elasticsearch repository for genre documents."""

    async def get_sorted_genres(
        self,
        page_number: int,
        page_size: int,
        sort_str: str | None = None,
    ) -> list[dict]:
        """Return a paginated and sorted list of genre documents."""
        if sort_str:
            order = "desc" if sort_str.startswith("-") else "asc"
            clean_field = sort_str.lstrip("-")
            field = "name.raw" if clean_field == "name" else clean_field
            sort = {field: order}
        else:
            sort = {"name.raw": "asc"}

        return await self.get_filtered(
            page_number=page_number,
            page_size=page_size,
            query={"match_all": {}},
            sort=sort,
        )
