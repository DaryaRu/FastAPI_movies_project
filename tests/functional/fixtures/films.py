"""Fixture for tests /films endpoints."""

import pytest_asyncio

from functional.settings import test_settings
from functional.testdata.es_mapping import (
    MOVIES_INDEX_SCHEMA,
    PERSON_INDEX_SCHEMA,
)
from functional.testdata.films import FILMS_DATA, TEST_PERSON_ID


@pytest_asyncio.fixture(scope="session", autouse=True)
async def film_data(es_write_data):
    """Load films and persons test data into Elasticsearch."""
    person_data = [
        {
            "id": TEST_PERSON_ID,
            "name": "Ann",
            "films": [
                {"id": film["id"], "roles": ["actor"]} for film in FILMS_DATA
            ],
        }
    ]
    await es_write_data(
        test_settings.elastic_movies_index,
        MOVIES_INDEX_SCHEMA,
        FILMS_DATA,
    )
    await es_write_data(
        test_settings.elastic_persons_index,
        PERSON_INDEX_SCHEMA,
        person_data,
    )
