"""Genres API endpoint router.

Provides routes for paginated genre listing, sorting,
and fetching specific genre details by unique identifier.
"""

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_cache.decorator import cache

from api.v1.dependencies import PaginationDepend
from core import config
from schemas.genres import GenreResponse as Genre
from services.genres import GenreService, get_genre_service

router = APIRouter()


@router.get(
    "/", response_model=list[Genre], summary="Получить список всех жанров"
)
@cache(expire=config.CACHE_EXPIRE)
async def genre_list(
    pagination: PaginationDepend,
    genre_service: GenreService = Depends(get_genre_service),
    sort: str | None = Query(
        None,
        description="Сортировка по имени по алфавиту (name и -name)",
    ),
) -> list[Genre]:
    """Get a paginated list of genres with optional sorting."""
    return await genre_service.get_list(
        page_size=pagination.page_size,
        page_number=pagination.page_number,
        sort=sort,
    )


@router.get(
    "/{genre_uuid}", response_model=Genre, summary="Получить жанр по UUID"
)
@cache(expire=config.CACHE_EXPIRE)
async def genre_details(
    genre_uuid: UUID, genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    """Get detailed information for a specific genre by its UUID."""
    genre = await genre_service.get_by_uuid(genre_uuid)
    if not genre:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="genre not found"
        )
    return genre
