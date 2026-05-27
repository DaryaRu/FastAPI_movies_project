"""Test film data for ES."""

import uuid

TEST_GENRE_ID = "3d8d3b6e-13c5-436f-89d7-ec4b055536d4"
TEST_PERSON_ID = "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95"
FILM_DATA_LIST_LENGTH = 60

FILMS_DATA = [
    {
        "id": str(uuid.uuid4()),
        "title": f"The Star Part {i}",
        "imdb_rating": float(1.0 + (i / 10)),
        "description": f"Description number {i}",
        "directors": [],
        "actors": [{"id": TEST_PERSON_ID, "name": "Ann"}],
        "writers": [],
        "genres": [{"id": TEST_GENRE_ID, "name": "Action"}],
    }
    for i in range(FILM_DATA_LIST_LENGTH)
]
