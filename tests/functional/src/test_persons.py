from typing import Callable, NamedTuple
import aiohttp
import pytest

from functional.settings import test_settings

<<<<<<< HEAD
PERSONS_PATH = "persons/"
=======
PERSONS_PATH = f"{test_settings.api_prefix}/persons"
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2


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
<<<<<<< HEAD
        url = f'{PERSONS_PATH}search'
=======
        url = f'{PERSONS_PATH}/search'
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2
        response = await http_client.get(url, params=case.query)
        body = await response.json()
        assert response.status == case.status_code
        assert len(body) == case.length
        
        
class TestPersonDetails:
    async def test_person_details_ok(
        self,
        http_client: aiohttp.ClientSession,
        person_data: list[dict],
    ) -> None:
        person = person_data[0]
        person_id = person["id"]

<<<<<<< HEAD
        url = f"{PERSONS_PATH}{person_id}/"
=======
        url = f"{PERSONS_PATH}/{person_id}/"
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2

        response = await http_client.get(url)
        body = await response.json()
        assert response.status == 200
        assert body["uuid"] == person_id
        assert body["full_name"] == person["name"]
        assert len(body["films"]) == len(person["films"])
        
    async def test_person_details_not_found(
        self,
        http_client: aiohttp.ClientSession,
    ):
        fake_uuid = "11111111-1111-1111-1111-111111111111"

<<<<<<< HEAD
        url = f"{PERSONS_PATH}{fake_uuid}/"
=======
        url = f"{PERSONS_PATH}/{fake_uuid}/"
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2

        response = await http_client.get(url)
        body = await response.json()

        assert response.status == 404
        assert body["detail"] == "person not found"
        
    async def test_person_details_invalid_uuid(
        self,
        http_client: aiohttp.ClientSession,
    ):
<<<<<<< HEAD
        url = f"{PERSONS_PATH}invalid-uuid/"
=======
        url = f"{PERSONS_PATH}/invalid-uuid/"
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2

        response = await http_client.get(url)
        assert response.status == 422
        
        
class TestPersonCache:
    @pytest.mark.parametrize(
        'path',
        [
<<<<<<< HEAD
            lambda pid: f"{PERSONS_PATH}{pid}/",
            lambda _: f"{PERSONS_PATH}search?query=Tom",
            lambda _: {PERSONS_PATH}",
=======
            lambda pid: f"{PERSONS_PATH}/{pid}/",
            lambda _: f"{PERSONS_PATH}/search?query=Tom",
            lambda _: f"{PERSONS_PATH}/",
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2
        ],
    )   
    async def test_person_details_cache(
        self,
        http_client: aiohttp.ClientSession,
        person_data: list[dict],
        path: Callable[[str], str],
    ):
        person_id = person_data[0]["id"]
<<<<<<< HEAD
        url = test_settings.service_url + path(person_id)
=======
        url = path(person_id)
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2

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
<<<<<<< HEAD
            ({"page_number": 1, "page_size": test_settings.service_max_page_size + 1}, "page_size"),
=======
            ({"page_number": 1, "page_size": test_settings.pagination_max_page_size + 1}, "page_size"),
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2
        ],
    )
    async def test_person_list_invalid_pagination(
        self,
        http_client: aiohttp.ClientSession,
        query: dict,
        expected_field: str,
    ):
        params = "&".join([f"{k}={v}" for k, v in query.items()])
<<<<<<< HEAD
        url = f"{PERSONS_PATH}?{params}"
=======
        url = f"{PERSONS_PATH}/?{params}"
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2

        response = await http_client.get(url)
        body = await response.json()

        assert response.status == 422
        assert expected_field in str(body)
        
    async def test_person_list_pagination_different_pages(
        self,
        http_client: aiohttp.ClientSession,
    ):
<<<<<<< HEAD
        url1 = f"{PERSONS_PATH}?page_number=1&page_size=5"
        url2 = f"{PERSONS_PATH}?page_number=2&page_size=5"
=======
        url1 = f"{PERSONS_PATH}/?page_number=1&page_size=5"
        url2 = f"{PERSONS_PATH}/?page_number=2&page_size=5"
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2

        response_1 = await http_client.get(url1)
        body_1 = await response_1.json()

        response_2 = await http_client.get(url2)
        body_2 = await response_2.json()

        assert response_1.status == 200
        assert response_2.status == 200
        assert body_1 != body_2
        
    async def test_person_list_page_size(
        self,
        http_client: aiohttp.ClientSession,
    ):
<<<<<<< HEAD
        url = f"{PERSONS_PATH}?page_size=5&page_number=1"
=======
        url = f"{PERSONS_PATH}/?page_size=5&page_number=1"
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2

        response = await http_client.get(url)
        body = await response.json()

        assert response.status == 200
<<<<<<< HEAD
        assert len(body) <= 5
=======
        assert len(body) == 5
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2
        
    async def test_person_list_ok(
        self,
        http_client: aiohttp.ClientSession,
    ):
<<<<<<< HEAD
        url = PERSONS_PATH
=======
        url = f"{PERSONS_PATH}/"
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2

        response = await http_client.get(url)
        body = await response.json()

        assert response.status == 200
<<<<<<< HEAD
        assert len(body) <= test_settings.service_default_page_size
=======
        assert len(body) <= test_settings.pagination_default_page_size
>>>>>>> 44ab9759d631e7977170e096a5a71b68dc2ac7e2
