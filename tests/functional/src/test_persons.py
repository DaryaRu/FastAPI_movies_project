from typing import Callable, NamedTuple
import aiohttp
import pytest

from functional.settings import test_settings
from tests.functional.utils.check_methods import (
    assert_status_return_json,
)

PERSONS_PATH = f"{test_settings.api_prefix}/persons"


class SearchCase(NamedTuple):
    query: dict[str, str]
    status_code: int
    length: int


class TestPersonSearch:
    @pytest.mark.parametrize(
        'case',
        [
            SearchCase({'query': 'Tom'}, 200, 3),
            SearchCase({'query': 'Emma'}, 200, 2),
            SearchCase({'query': 'Chris'}, 200, 3),
            SearchCase({'query': 'Robert'}, 200, 2),
            SearchCase({'query': 'NonExistingPerson'}, 200, 0),
        ]
    )
    async def test_search_persons(
        self,
        http_client: aiohttp.ClientSession,
        case: SearchCase,
    ) -> None:
        url = f'{PERSONS_PATH}/search'
        response = await http_client.get(url, params=case.query)
        body = await assert_status_return_json(response, case.status_code)
        assert len(body) == case.length


class TestPersonDetails:
    async def test_person_details_ok(
        self,
        http_client: aiohttp.ClientSession,
        person_data: list[dict],
    ) -> None:
        person = person_data[0]
        person_id = person["id"]

        url = f"{PERSONS_PATH}/{person_id}/"

        response = await http_client.get(url)
        body = await assert_status_return_json(response, 200)
        assert body["uuid"] == person_id
        assert body["full_name"] == person["name"]
        assert len(body["films"]) == len(person["films"])

    async def test_person_details_not_found(
        self,
        http_client: aiohttp.ClientSession,
    ):
        fake_uuid = "11111111-1111-1111-1111-111111111111"

        url = f"{PERSONS_PATH}/{fake_uuid}/"

        response = await http_client.get(url)
        body = await assert_status_return_json(response, 404)

        assert body["detail"] == "person not found"

    async def test_person_details_invalid_uuid(
        self,
        http_client: aiohttp.ClientSession,
    ):
        url = f"{PERSONS_PATH}/invalid-uuid/"

        response = await http_client.get(url)
        assert response.status == 422


class TestPersonCache:
    @pytest.mark.parametrize(
        'path',
        [
            lambda pid: f"{PERSONS_PATH}/{pid}/",
            lambda _: f"{PERSONS_PATH}/search?query=Tom",
            lambda _: f"{PERSONS_PATH}/",
        ],
    )
    async def test_person_details_cache(
        self,
        http_client: aiohttp.ClientSession,
        person_data: list[dict],
        path: Callable[[str], str],
    ):
        person_id = person_data[0]["id"]
        url = path(person_id)

        response = await http_client.get(url)
        first_body = await response.json()
        first_cache = response.headers.get("X-FastAPI-Cache")

        response = await http_client.get(url)
        second_body = await response.json()
        second_cache = response.headers.get("X-FastAPI-Cache")

        assert first_body == second_body

        assert first_cache == "MISS"
        assert second_cache == "HIT"


class TestPersonList:
    @pytest.mark.parametrize(
        "query, expected_field",
        [
            ({"page_number": 0, "page_size": 10}, "page_number"),
            ({"page_number": 1, "page_size": 0}, "page_size"),
            (
                {
                    "page_number": 1,
                    "page_size": test_settings.pagination_max_page_size + 1,
                },
                "page_size",
            ),
        ],
    )
    async def test_person_list_invalid_pagination(
        self,
        http_client: aiohttp.ClientSession,
        query: dict,
        expected_field: str,
    ):
        params = "&".join([f"{k}={v}" for k, v in query.items()])
        url = f"{PERSONS_PATH}/?{params}"

        response = await http_client.get(url)
        body = await assert_status_return_json(response, 422)

        assert expected_field in str(body)

    async def test_person_list_pagination_different_pages(
        self,
        http_client: aiohttp.ClientSession,
    ):
        url1 = f"{PERSONS_PATH}/?page_number=1&page_size=5"
        url2 = f"{PERSONS_PATH}/?page_number=2&page_size=5"

        response_1 = await http_client.get(url1)

        response_2 = await http_client.get(url2)

        body_1 = await assert_status_return_json(response_1, 200)
        body_2 = await assert_status_return_json(response_2, 200)
        assert body_1 != body_2

    async def test_person_list_page_size(
        self,
        http_client: aiohttp.ClientSession,
    ):
        url = f"{PERSONS_PATH}/?page_size=5&page_number=1"

        response = await http_client.get(url)
        body = await assert_status_return_json(response, 200)
        assert len(body) == 5

    async def test_person_list_ok(
        self,
        http_client: aiohttp.ClientSession,
    ):
        url = f"{PERSONS_PATH}/"

        response = await http_client.get(url)
        body = await assert_status_return_json(response, 200)
        assert len(body) <= test_settings.pagination_default_page_size
