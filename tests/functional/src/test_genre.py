"""Functional tests for /api/v1/genres endpoints."""

import pytest
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

    @pytest.mark.parametrize(
        "query_data,expected_answer",
        [
            (
                {"genre_id": GENRE_ID},
                {"status": 200, "uuid": GENRE_ID, "name": GENRES_DATA[0]["name"]},
            ),
            (
                {"genre_id": UNKNOWN_ID},
                {"status": 404},
            ),
        ],
    )
    async def test_genre_detail(
        self, http_client: AsyncClient, query_data: dict, expected_answer: dict
    ):
        response = await http_client.get(f"/api/v1/genres/{query_data['genre_id']}")
        assert response.status_code == expected_answer["status"]
        if response.status_code == 200:
            data = response.json()
            assert data["uuid"] == expected_answer["uuid"]
            assert data["name"] == expected_answer["name"]


class TestGenreDetailValidation:
    """Test UUID validation."""

    @pytest.mark.parametrize(
        "query_data,expected_answer",
        [
            ("true", 422),
            ("111", 422),
            ("00000000-0000-0000-0000-00000000000Z", 422),
        ],
    )
    async def test_invalid_uuid_returns_422(
        self, http_client: AsyncClient, query_data: str, expected_answer: int
    ):
        response = await http_client.get(f"/api/v1/genres/{query_data}")
        assert response.status_code == expected_answer


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


class TestGenreListSorting:
    """Tests for sort query parameter."""

    @pytest.mark.parametrize(
        "query_data,expected",
        [
            ({"sort": "name"}, sorted([g["name"] for g in GENRES_DATA])),
            ({"sort": "-name"}, sorted([g["name"] for g in GENRES_DATA], reverse=True)),
        ],
    )
    async def test_sort_returns_sorted_list(
        self, http_client: AsyncClient, query_data: dict, expected: list
    ):
        response = await http_client.get("/api/v1/genres/", params=query_data)
        assert response.status_code == 200
        names = [g["name"] for g in response.json()]
        assert names == expected

    @pytest.mark.parametrize("sort", ["id", "uuid"])
    async def test_invalid_sort_returns_422(self, http_client: AsyncClient, sort: str):
        response = await http_client.get("/api/v1/genres/", params={"sort": sort})
        assert response.status_code == 422
