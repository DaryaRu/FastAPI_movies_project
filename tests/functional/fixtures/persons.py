from typing import Any, Awaitable, Callable
import random
import uuid

import pytest
import pytest_asyncio

from settings import test_settings


@pytest.fixture(scope='session')
def person_data() -> list[dict]:
    names = [
        'Tom Hardy', 'Tom Hanks', 'Tom Holland', 'Thomas Shelby',
        'Emma Stone', 'Emma Watson', 'Emily Blunt', 'Emily Watson',
        'John Wick', 'Johnny Depp', 'John Travolta', 'John Krasinski',
        'Will Smith', 'Will Ferrell', 'William Turner', 'Bill Murray',
        'Brad Pitt', 'Bradley Cooper', 'Leonardo DiCaprio', 'Leo Tolstoy',
        'Chris Evans', 'Chris Hemsworth', 'Chris Pratt', 'Christian Bale',
        'Robert Downey Jr', 'Robert Pattinson', 'Rob Stark', 'Robin Williams',
        'Scarlett Johansson', 'Scarlett Byrne', 'Jennifer Lawrence', 'Jennifer Aniston',
        'Michael Jordan', 'Michael Fassbender', 'Michelle Yeoh', 'Mike Tyson',
        'Anna Kendrick', 'Anne Hathaway', 'Anabelle Wallis', 'Ann Wilson',
        'Daniel Craig', 'Daniel Radcliffe', 'Dan Stevens', 'Danny DeVito',
        'Kate Winslet', 'Katie Holmes', 'Katherine Langford', 'Kevin Hart',
        'Samuel Jackson', 'Sam Worthington', 'Samantha Morton', 'Sandra Bullock',
        'Natalie Portman', 'Nathan Drake', 'Nicole Kidman', 'Nicolas Cage',
        'Peter Parker', 'Piers Brosnan', 'Paul Walker', 'Pam Beesly',
    ]
    roles = ['actor', 'director', 'writer']
    es_data = [{
        'id': str(uuid.uuid4()),
        'name': name,
        'films': [
            {
                'id': str(uuid.uuid4()),
                'roles': random.sample(
                    roles,
                    k=random.randint(1, len(roles)),
                ),
            }
            for _ in range(random.randint(1, 5))
        ],
    } for name in names]
    return es_data


@pytest_asyncio.fixture(scope='session', autouse=True)
async def load_person_data_to_es(
    es_write_data: Callable[[list[dict], str, dict, dict], Awaitable[list[Any]],],
    person_data: list[dict]
) -> None:
    bulk_query: list[dict] = []
    for row in person_data:
        data = {'_index': test_settings.es_person_index, '_id': row['id']}
        data.update({'_source': row})
        bulk_query.append(data)
    await es_write_data(
        bulk_query,
        test_settings.es_person_index,
        test_settings.es_person_index_mapping,
        test_settings.es_index_settings,
    )
