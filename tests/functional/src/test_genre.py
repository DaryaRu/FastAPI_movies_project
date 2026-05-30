"""Functional tests for /api/v1/genres endpoints."""

import pytest
from aiohttp import ClientSession

from functional.settings import test_settings
from functional.testdata.genres import GENRES_DATA
from tests.functional.utils.check_methods import (
    assert_required_fields,
    assert_status_return_json,
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
        data = await assert_status_return_json(
            response, expected_answer["status"]
            )
        if response.status == 200:
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
        data = await assert_status_return_json(response, 200)
        assert isinstance(data, list)
        assert len(data) == len(GENRES_DATA)

    async def test_response_has_required_fields(
        self, http_client: ClientSession
    ):
        response = await http_client.get(GENRES_URL)
        data = await assert_status_return_json(response, 200)
        genre = data[0]
        expected_fields = {"uuid", "name"}
        assert_required_fields(genre, expected_fields)


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
        data = await assert_status_return_json(response, 200)
        names = [g["name"] for g in data]
        assert names == expected

    @pytest.mark.parametrize("sort", ["id", "uuid"])
    async def test_invalid_sort_returns_422(
        self, http_client: ClientSession, sort: str
    ):
        response = await http_client.get(GENRES_URL, params={"sort": sort})
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
        first_body = await response_from_es.json()
        first_cache = response_from_es.headers.get("X-FastAPI-Cache")

        response_from_cache = await http_client.get(url)
        second_body = await response_from_cache.json()
        second_cache = response_from_cache.headers.get("X-FastAPI-Cache")

        assert first_body == second_body
        assert first_cache == "MISS"
        assert second_cache == "HIT"

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
        data_first_page = await assert_status_return_json(
            response_first_page, 200
            )
        data_second_page = await assert_status_return_json(
            response_second_page, 200
            )

        assert data_first_page != data_second_page


class TestGenreListPaginationValidation:
    """Tests for pagination query parameters."""

    @pytest.mark.parametrize(
        "query_data,expected_answer",
        [
            ({"page_number": 0}, 422),
            ({"page_number": -1}, 422),
            ({"page_number": -100}, 422),
            ({"page_size": 0}, 422),
            ({"page_size": -1}, 422),
            ({"page_size": 101}, 422),
            ({"page_size": 1000}, 422),
            ({"page_number": "abc"}, 422),
        ],
    )
    async def test_invalid_pagination_returns_422(
        self,
        http_client: ClientSession,
        query_data: dict,
        expected_answer: int,
    ):
        response = await http_client.get(GENRES_URL, params=query_data)
        assert response.status == expected_answer

    @pytest.mark.parametrize(
        "query_data,expected_answer",
        [
            ({"page_size": 1}, {"status": 200, "count": 1}),
            ({"page_size": 100}, {"status": 200}),
            ({"page_number": 9999}, {"status": 200, "body": []}),
        ],
    )
    async def test_valid_pagination_returns_200(
        self,
        http_client: ClientSession,
        query_data: dict,
        expected_answer: dict,
    ):
        response = await http_client.get(GENRES_URL, params=query_data)
        data = await assert_status_return_json(
            response, expected_answer["status"]
            )
        if "count" in expected_answer or "body" in expected_answer:
            if "count" in expected_answer:
                assert len(data) == expected_answer["count"]
            if "body" in expected_answer:
                assert data == expected_answer["body"]
