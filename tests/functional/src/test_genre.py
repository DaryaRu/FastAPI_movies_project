"""Functional tests for /api/v1/genres endpoints."""

import pytest
import pytest_asyncio
from aiohttp import ClientSession

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


GENRES_URL = f"{test_settings.api_prefix}/genres"

GENRE_ID = GENRES_DATA[0]["id"]
UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


class TestGenreDetail:
    """Tests for GET /api/v1/genres/{genre_id}."""

    @pytest.mark.parametrize(
        "query_data,expected_answer",
        [
            (
                {"genre_id": GENRE_ID},
                {
                    "status": 200,
                    "uuid": GENRE_ID,
                    "name": GENRES_DATA[0]["name"],
                },
            ),
            (
                {"genre_id": UNKNOWN_ID},
                {"status": 404},
            ),
        ],
    )
    async def test_genre_detail(
        self,
        http_client: ClientSession,
        query_data: dict,
        expected_answer: dict,
    ):
        response = await http_client.get(
            f"{GENRES_URL}/{query_data['genre_id']}"
        )
        assert response.status == expected_answer["status"]
        if response.status == 200:
            data = await response.json()
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
        self,
        http_client: ClientSession,
        query_data: str,
        expected_answer: int,
    ):
        response = await http_client.get(f"{GENRES_URL}/{query_data}")
        assert response.status == expected_answer


class TestGenreList:
    """Tests for GET /api/v1/genres/."""

    async def test_returns_200(self, http_client: ClientSession):
        response = await http_client.get(GENRES_URL)
        assert response.status == 200

    async def test_returns_all_genres(self, http_client: ClientSession):
        response = await http_client.get(GENRES_URL)
        data = await response.json()
        assert isinstance(data, list)
        assert len(data) == len(GENRES_DATA)

    async def test_response_has_required_fields(
        self, http_client: ClientSession
    ):
        response = await http_client.get(GENRES_URL)
        data = await response.json()
        genre = data[0]
        assert "uuid" in genre
        assert "name" in genre


class TestGenreListSorting:
    """Tests for sort query parameter."""

    @pytest.mark.parametrize(
        "query_data,expected",
        [
            (
                {"sort": "name"},
                sorted([g["name"] for g in GENRES_DATA]),
            ),
            (
                {"sort": "-name"},
                sorted([g["name"] for g in GENRES_DATA], reverse=True),
            ),
        ],
    )
    async def test_sort_returns_sorted_list(
        self,
        http_client: ClientSession,
        query_data: dict,
        expected: list,
    ):
        response = await http_client.get(GENRES_URL, params=query_data)
        assert response.status == 200
        data = await response.json()
        names = [g["name"] for g in data]
        assert names == expected

    @pytest.mark.parametrize("sort", ["id", "uuid"])
    async def test_invalid_sort_returns_422(
        self, http_client: ClientSession, sort: str
    ):
        response = await http_client.get(
            GENRES_URL, params={"sort": sort}
        )
        assert response.status == 422


class TestGenreCache:
    """Tests Redis cache."""

    @pytest.mark.parametrize(
        "url",
        [
            f"{GENRES_URL}/{GENRE_ID}",
            GENRES_URL,
        ],
    )
    async def test_repeated_request_responses_cache(
        self, http_client: ClientSession, url: str
    ):
        response_from_es = await http_client.get(url)
        response_from_cache = await http_client.get(url)
        assert (
            await response_from_es.json() == await response_from_cache.json()
        )
        assert float(response_from_cache.headers["X-Process-Time"]) < float(
            response_from_es.headers["X-Process-Time"]
        )

    async def test_different_sort_params_cache(
        self, http_client: ClientSession
    ):
        response_sorted_asc = await http_client.get(
            GENRES_URL, params={"sort": "name"}
        )
        response_sorted_desc = await http_client.get(
            GENRES_URL, params={"sort": "-name"}
        )
        assert (
            await response_sorted_asc.json()
            != await response_sorted_desc.json()
        )

    async def test_different_pages_cache(self, http_client: ClientSession):
        response_first_page = await http_client.get(
            GENRES_URL, params={"page_size": 1, "page_number": 1}
        )
        response_second_page = await http_client.get(
            GENRES_URL, params={"page_size": 1, "page_number": 2}
        )
        assert (
            await response_first_page.json()
            != await response_second_page.json()
        )
