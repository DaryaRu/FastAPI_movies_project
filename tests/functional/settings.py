from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    es_host: str = Field('http://127.0.0.1:9200', env='ELASTIC_HOST')
    es_film_index: str = Field('', env='ES_FILM_INDEX')
    es_genre_index: str = Field('', env='ES_GENRE_INDEX')
    es_person_index: str = Field('', env='ES_PERSON_INDEX')

    redis_host: str = Field('127.0.0.1', env='REDIS_HOST')
    redis_port: int = Field(6379, env='REDIS_PORT')
    
    service_max_page_size: int = Field(100, env='SERVICE_MAX_PAGE_SIZE')
    service_default_page_size: int = Field(100, env='SERVICE_DEFAULT_PAGE_SIZE')
    service_url: str = Field('http://test.com', env='SERVICE_URL')
    
    @property
    def es_index_settings(self):
        return {
            "refresh_interval": "1s",
            "analysis": {
                "filter": {
                    "english_stop": {"type": "stop", "stopwords": "_english_"},
                    "english_stemmer": {"type": "stemmer", "language": "english"},
                    "english_possessive_stemmer": {
                        "type": "stemmer",
                        "language": "possessive_english",
                    },
                    "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                    "russian_stemmer": {"type": "stemmer", "language": "russian"},
                },
                "analyzer": {
                    "ru_en": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stop",
                            "english_stemmer",
                            "english_possessive_stemmer",
                            "russian_stop",
                            "russian_stemmer",
                        ],
                    }
                },
            },
        }
        
    @property
    def es_person_index_mapping(self):
        return {
            "dynamic": "strict",
            "properties": {
                "id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "ru_en",
                    "fields": {"raw": {"type": "keyword"}},
                },
                "films": {
                    "type": "nested",
                    "dynamic": "strict",
                    "properties": {
                        "id": {"type": "keyword"},
                        "roles": {"type": "keyword"},
                    },
                },
            },
        }
 

test_settings = TestSettings()
print(test_settings.__dict__)
