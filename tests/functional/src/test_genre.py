"""Functional tests for /api/v1/genres endpoints."""

import pytest_asyncio
from httpx import AsyncClient

from functional.settings import test_settings
from functional.testdata.es_mapping import GENRE_INDEX_SCHEMA
from functional.testdata.genres import GENRES_DATA


@pytest_asyncio.fixture(scope="session", autouse=True)
async def genre_data(es_write_data):
    """Load genre test data into Elasticsearch."""
    await es_write_data(
        test_settings.elastic_genres_index,
        GENRE_INDEX_SCHEMA,
        GENRES_DATA,
    )


GENRE_ID = GENRES_DATA[0]["id"]
UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


class TestGenreDetail:
    """Tests for GET /api/v1/genres/{genre_id}."""

    async def test_returns_200(self, http_client: AsyncClient):
        response = await http_client.get(f"/api/v1/genres/{GENRE_ID}")
        assert response.status_code == 200

    async def test_returns_correct_data(self, http_client: AsyncClient):
        response = await http_client.get(f"/api/v1/genres/{GENRE_ID}")
        data = response.json()
        assert data["uuid"] == GENRE_ID
        assert data["name"] == GENRES_DATA[0]["name"]

    async def test_not_found(self, http_client: AsyncClient):
        response = await http_client.get(f"/api/v1/genres/{UNKNOWN_ID}")
        assert response.status_code == 404


class TestGenreList:
    """Tests for GET /api/v1/genres/."""

    async def test_returns_200(self, http_client: AsyncClient):
        response = await http_client.get("/api/v1/genres/")
        assert response.status_code == 200

    async def test_returns_all_genres(self, http_client: AsyncClient):
        response = await http_client.get("/api/v1/genres/")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(GENRES_DATA)

    async def test_response_has_required_fields(self, http_client: AsyncClient):
        response = await http_client.get("/api/v1/genres/")
        data = response.json()
        genre = data[0]
        assert "uuid" in genre
        assert "name" in genre
