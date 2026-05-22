"""Test settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    """Settings for tests."""

    model_config = SettingsConfigDict(env_file=".env")

    elastic_host: str = Field(alias="ELASTIC_HOST")
    elastic_port: int = Field(default=9200, alias="ELASTIC_PORT")
    elastic_movies_index: str = Field(
        default="movies", alias="ELASTIC_FILM_INDEX"
    )
    elastic_genres_index: str = Field(
        default="genres", alias="ELASTIC_GENRE_INDEX"
    )
    elastic_persons_index: str = Field(
        default="persons", alias="ELASTIC_PERSON_INDEX"
    )

    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    api_url: str = Field(default="http://localhost:7000", alias="API_URL")


test_settings = TestSettings()
