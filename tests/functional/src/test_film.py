"""Functional tests for /api/v1/films endpoints."""

import pytest
from aiohttp import ClientSession

from functional.settings import test_settings
from functional.testdata.films import FILMS_DATA, TEST_GENRE_ID, \
                                      TEST_PERSON_ID, FILM_DATA_LIST_LENGTH


FILMS_URL = f"{test_settings.api_prefix}/films"
PERSON_FILMS_URL = f"{test_settings.api_prefix}/persons/{TEST_PERSON_ID}/film"
UNKNOWN_UUID = "00000000-0000-0000-0000-000000000000"
INVALID_UUID = "not-a-valid-uuid-123"
ERR_FILM_NOT_FOUND = {"detail": "film not found"}
ERR_PERSON_NOT_FOUND = {"detail": "person not found"}
PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50


class TestFilmDetail:
    """Tests for GET /api/v1/films/{film_id}."""

    @pytest.mark.parametrize(
        "query_data,expected_status",
        [
            (
                {"film_id": FILMS_DATA[0]["id"]},
                200
            ),
            (
                {"film_id": UNKNOWN_UUID},
                404
            ),
            (
                {"film_id": INVALID_UUID},
                422
            ),
        ],
    )
    async def test_film_detail(
        self,
        http_client: ClientSession,
        query_data: dict,
        expected_status: int,
    ):
        film_id = query_data["film_id"]
        response = await http_client.get(f"{FILMS_URL}/{film_id}")

        assert response.status == expected_status

        if response.status == 200:
            data = await response.json()
            
            expected_fields = {
                "uuid", "title", "imdb_rating", "description",
                "creation_date", "directors", "actors", "writers", "genre"
            }
            assert expected_fields.issubset(data.keys()), (
                f"Missing fields: {expected_fields - data.keys()}"
            )

            assert isinstance(data["title"], str)
            assert (
                isinstance(data["imdb_rating"], (float, int))
                or data["imdb_rating"] is None
            )
            assert (
                isinstance(data["description"], str)
                or data["description"] is None
            )

            expected_film = FILMS_DATA[0]
            assert data["uuid"] == expected_film["id"]
            assert data["title"] == expected_film["title"]
            assert data["imdb_rating"] == expected_film["imdb_rating"]
            assert data["description"] == expected_film["description"]

            assert len(data["genre"]) == 1
            genre = data["genre"][0]
            assert isinstance(genre, dict)
            assert "uuid" in genre and "name" in genre
            assert genre["uuid"] == TEST_GENRE_ID
            assert genre["name"] == "Action"

            assert len(data["actors"]) == 1
            actor = data["actors"][0]
            assert isinstance(actor, dict)
            assert "uuid" in actor and "full_name" in actor
            assert actor["full_name"] == "Ann"

            assert isinstance(data["directors"], list)
            assert isinstance(data["writers"], list)

        elif response.status == 404:
            data = await response.json()
            assert data == ERR_FILM_NOT_FOUND


class TestFilmDetailValidation:
    """Test UUID validation film detail query data."""

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
        response = await http_client.get(f"{FILMS_URL}/{query_data}")
        assert response.status == expected_answer


class TestFilmList:
    """Tests for GET /api/v1/films."""

    async def test_film_list_returns_200(self, http_client: ClientSession):
        response = await http_client.get(FILMS_URL)
        assert response.status == 200

    async def test_returns_all_films(self, http_client: ClientSession):
        response = await http_client.get(
            FILMS_URL,
            params={"page_size": PAGE_SIZE}
            )
        data = await response.json()
        assert isinstance(data, list)
        assert len(data) == len(FILMS_DATA)

    async def test_films_list_film_info(
            self,
            http_client: ClientSession
            ):
        response = await http_client.get(FILMS_URL)
        assert response.status == 200
        data = await response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        first_film = data[0]

        expected_fields = {"uuid", "title", "imdb_rating"}
        assert expected_fields.issubset(first_film.keys()), (
            f"Missing fields: {expected_fields - first_film.keys()}"
        )

        assert isinstance(first_film["title"], str)
        assert (
            isinstance(first_film["imdb_rating"], (float, int))
            or first_film["imdb_rating"] is None
        )

        from functional.fixtures.films import FILMS_DATA
        expected_film = FILMS_DATA[0]

        assert first_film["uuid"] == expected_film["id"]
        assert first_film["title"] == expected_film["title"]
        assert first_film["imdb_rating"] == expected_film["imdb_rating"]

    async def test_films_list_filter_by_genre(
            self,
            http_client: ClientSession
            ):
        response = await http_client.get(
            FILMS_URL,
            params={"filter[genre]": TEST_GENRE_ID, "page_size": PAGE_SIZE}
        )
        assert response.status == 200

        data = await response.json()
        assert isinstance(data, list)
        assert len(data) == len(FILMS_DATA)

    async def test_films_list_invalid_genre_uuid(
            self,
            http_client: ClientSession
            ):
        response = await http_client.get(
            FILMS_URL,
            params={"filter[genre]": INVALID_UUID}
        )
        assert response.status == 422


class TestFilmListSorting:
    """Tests for sort query parameter in films endpoint."""

    @pytest.mark.parametrize(
        "query_data,expected_order",
        [
            (
                {"sort": "imdb_rating", "page_size": PAGE_SIZE},
                sorted([f["imdb_rating"] for f in FILMS_DATA]),
            ),
            (
                {"sort": "-imdb_rating", "page_size": PAGE_SIZE},
                sorted([f["imdb_rating"] for f in FILMS_DATA], reverse=True),
            ),
        ],
    )
    async def test_sort_returns_sorted_film_list(
        self,
        http_client: ClientSession,
        query_data: dict,
        expected_order: list,
    ):
        response = await http_client.get(FILMS_URL, params=query_data)
        assert response.status == 200
        data = await response.json()
        ratings = [f["imdb_rating"] for f in data]
        assert ratings == expected_order

    @pytest.mark.parametrize("sort", ["id", "description", "invalid_field"])
    async def test_invalid_sort_returns_422(
        self, http_client: ClientSession, sort: str
    ):
        response = await http_client.get(FILMS_URL, params={"sort": sort})
        assert response.status == 422


class TestFilmListPaginationValidation:
    """Tests for pagination query parameters."""

    @pytest.mark.parametrize(
        "query_data,expected_answer",
        [
            ({"page_number": 0}, 422),
            ({"page_number": -1}, 422),
            ({"page_size": 0}, 422),
            ({"page_size": -1}, 422),
            ({"page_size": 101}, 422),
            ({"page_size": 1000000}, 422),
            ({"page_number": "abc"}, 422),
        ],
    )
    async def test_invalid_pagination_returns_422(
        self,
        http_client: ClientSession,
        query_data: dict,
        expected_answer: int,
    ):
        response = await http_client.get(FILMS_URL, params=query_data)
        assert response.status == expected_answer

    @pytest.mark.parametrize(
        "query_data,expected_answer",
        [
            (
                {"page_size": 1},
                {"status": 200, "count": 1}
            ),
            (
                {"page_size": 100},
                {"status": 200, "count": FILM_DATA_LIST_LENGTH}
            ),
            (
                {},
                {"status": 200, "count": DEFAULT_PAGE_SIZE}
            ),
            (
                {"page_number": 9999},
                {"status": 200, "body": []}
            ),
        ],
    )
    async def test_valid_pagination_returns_200(
        self,
        http_client: ClientSession,
        query_data: dict,
        expected_answer: dict,
    ):
        response = await http_client.get(FILMS_URL, params=query_data)
        assert response.status == expected_answer["status"]
        data = await response.json()
        assert isinstance(data, list)

        if "count" in expected_answer:
            assert len(data) == expected_answer["count"]

        if "body" in expected_answer:
            assert data == expected_answer["body"]


class TestFilmForPerson:
    """Tests for GET /api/v1/persons/{person_uuid}/film."""

    async def test_returns_200_for_valid_person(
        self,
        http_client: ClientSession,
    ):
        response = await http_client.get(PERSON_FILMS_URL)
        assert response.status == 200

    async def test_returns_all_films_for_person(
        self,
        http_client: ClientSession
    ):
        response = await http_client.get(
            PERSON_FILMS_URL,
            params={"page_size": FILM_DATA_LIST_LENGTH}
        )
        assert response.status == 200
        data = await response.json()
        assert isinstance(data, list)
        assert len(data) == len(FILMS_DATA)

    async def test_response_models_validation(
        self,
        http_client: ClientSession
    ):
        response = await http_client.get(
            PERSON_FILMS_URL,
            params={"page_size": 1}
            )
        assert response.status == 200
        data = await response.json()
        assert len(data) > 0
        film = data[0]

        expected_fields = {"uuid", "title", "imdb_rating"}
        assert expected_fields.issubset(film.keys()), (
            f"Missing fields: {expected_fields - film.keys()}"
        )

        assert isinstance(film["title"], str)
        assert (
            isinstance(film["imdb_rating"], (float, int))
            or film["imdb_rating"] is None
        )

        from functional.fixtures.films import FILMS_IDS
        assert film["uuid"] in FILMS_IDS

    async def test_unknown_person_returns_404(
        self,
        http_client: ClientSession
    ):
        url = f"{test_settings.api_prefix}/persons/{UNKNOWN_UUID}/film"
        response = await http_client.get(url)
        assert response.status == 404
        data = await response.json()
        assert data == ERR_PERSON_NOT_FOUND

    async def test_invalid_person_uuid_returns_422(
        self,
        http_client: ClientSession
    ):
        url = f"{test_settings.api_prefix}/persons/{INVALID_UUID}/film"
        response = await http_client.get(url)
        assert response.status == 422


class TestFilmCache:
    """Tests Redis cache for films endpoints."""

    @pytest.mark.parametrize(
        "url",
        [
            FILMS_URL,
            f"{FILMS_URL}/{FILMS_DATA[0]['id']}",
            f"{test_settings.api_prefix}/persons/{TEST_PERSON_ID}/film",
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

        assert float(response_from_cache.headers["X-Process-Time"]) < float(
            response_from_es.headers["X-Process-Time"]
        )

    async def test_different_sort_params_cache(
            self,
            http_client: ClientSession
            ):
        response_sorted_asc = await http_client.get(
            FILMS_URL, params={"sort": "imdb_rating",
                               "page_size": FILM_DATA_LIST_LENGTH}
        )
        response_sorted_desc = await http_client.get(
            FILMS_URL, params={"sort": "-imdb_rating",
                               "page_size": FILM_DATA_LIST_LENGTH}
        )

        assert (
            await response_sorted_asc.json()
            != await response_sorted_desc.json()
        )

    async def test_different_pages_cache(self, http_client: ClientSession):
        response_first_page = await http_client.get(
            FILMS_URL, params={"page_size": 1, "page_number": 1}
        )
        response_second_page = await http_client.get(
            FILMS_URL, params={"page_size": 1, "page_number": 2}
        )

        assert (
            await response_first_page.json()
            != await response_second_page.json()
        )

    async def test_different_genre_filters_cache(
            self,
            http_client: ClientSession
            ):

        response_action_genre = await http_client.get(
            FILMS_URL, params={"filter[genre]": TEST_GENRE_ID}
        )
        response_empty_genre = await http_client.get(
            FILMS_URL, params={"filter[genre]": UNKNOWN_UUID}
        )

        assert (
            await response_action_genre.json()
            != await response_empty_genre.json()
        )
