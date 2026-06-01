# FastAPI_sprint_1

В корневой папке необходим файл `.env` с переменными для инфраструктуры.
В папке `etl` необходим файл `.env` с переменными для работы сервиса.
В папке `src` необходим файл `.env` с переменными для работы сервиса.

## Архитектура API

FastAPI читает данные из Elasticsearch с кэшированием через Redis.

### Эндпоинты

- `GET /api/v1/films/` — список фильмов с сортировкой и фильтром по жанру
- `GET /api/v1/films/search/` — полнотекстовый поиск по фильмам
- `GET /api/v1/films/{uuid}/` — детали фильма
- `GET /api/v1/genres/` — список жанров
- `GET /api/v1/genres/{uuid}/` — детали жанра
- `GET /api/v1/persons/` — список персон
- `GET /api/v1/persons/search/` — полнотекстовый поиск по персонам
- `GET /api/v1/persons/{uuid}/` — детали персоны
- `GET /api/v1/persons/{uuid}/film/` — фильмы персоны

Документация: `/api/openapi`

### Структура

```
src/
├── main.py                  # FastAPI app, middleware, роутеры
├── core/
│   ├── config.py            # Настройки из переменных окружения
│   └── logger.py            # Конфигурация логирования
├── db/
│   ├── elastic.py           # Клиент Elasticsearch
│   └── redis.py             # Клиент Redis
├── api/v1/
│   ├── films.py             # Эндпоинты фильмов
│   ├── genres.py            # Эндпоинты жанров
│   └── persons.py           # Эндпоинты персон
├── services/
│   ├── film.py              # Бизнес-логика фильмов
│   ├── genres.py            # Бизнес-логика жанров
│   └── persons.py           # Бизнес-логика персон
├── repositories/
│   ├── base.py              # Базовый репозиторий Elasticsearch
│   ├── films.py             # Репозиторий фильмов
│   ├── genres.py            # Репозиторий жанров
│   └── persons.py           # Репозиторий персон
├── models/
│   ├── films.py             # Внутренние модели (данные из ES)
│   ├── genres.py
│   └── persons.py
├── schemas/
│   ├── films.py             # Схемы API-ответов
│   ├── film_shorts.py
│   ├── genres.py
│   └── persons.py
└── exceptions.py            # Исключения
```

### Слои приложения

- `Router` — валидация входных параметров, кэширование
- `Service` — бизнес-логика
- `Repository` — запросы к Elasticsearch
- `Schema` — сериализация ответа

### Кэширование

Все эндпоинты кэшируются через `fastapi-cache2` с Redis-бэкендом. Декоратор `@cache` стоит на уровне роутера. TTL задаётся переменной окружения `CACHE_EXPIRE`. Наличие кэша в ответе можно проверить по заголовку `X-FastAPI-Cache: HIT/MISS`.

### Устойчивость к сбоям

- **Elasticsearch недоступен** — все эндпоинты возвращают `503 Service Unavailable` с телом `{"detail": "search service unavailable"}`. Перед возвратом 503 репозиторий делает 3 попытки с экспоненциальным backoff.
- **Redis недоступен** — API продолжает работать без кэша. `FaultTolerantRedisBackend` перехватывает `ConnectionError` при чтении и записи: промах кэша обрабатывается как обычный запрос к Elasticsearch, результат не кэшируется.

### Модели и схемы

В проекте два слоя моделей:
- `models/` — внутренние модели с именами полей как в Elasticsearch (`id`, `name`)
- `schemas/` — API-схемы с именами полей для клиентов (`uuid`, `full_name`). Маппинг через `validation_alias`.


## Архитектура ETL

ETL-сервис переносит данные из PostgreSQL в Elasticsearch. Запускается в отдельном контейнере и работает в бесконечном цикле с паузой между итерациями (`ETL_POLL_INTERVAL`).

### Индексы Elasticsearch

- `movies` — фильмы с жанрами и персонами
- `genres` — жанры
- `persons` — персоны с фильмографией и ролями

### Структура

```
etl/
├── main.py                      # Точка входа, сборка зависимостей
├── config.py                    # Настройки из .env (pydantic-settings)
├── models.py                    # Pydantic-модели: FilmWork, Genre, Person
├── backoff.py                   # Декоратор повторных попыток
├── logging_config.py            # Настройка логирования
├── extract/
│   ├── postgres_extractor.py    # Извлечение данных из PostgreSQL
│   └── queries.py               # SQL-запросы
├── transform/
│   └── transformer.py           # Преобразование строк в Pydantic-модели
├── load/
│   ├── elastic.py               # Запись в Elasticsearch (bulk API)
│   └── es_schema.py             # Схемы индексов
├── pipeline/
│   └── orchestrator.py          # Координация этапов ETL
└── state/
    ├── base.py                  # Абстрактное хранилище состояния
    ├── json_storage.py          # Реализация через JSON-файл
    └── state.py                 # Менеджер состояния
```

### Пайплайн одной итерации (`run_once`)

Каждая итерация запускает пайплайны по схеме `PostgreSQL → Extract → Transform → Elasticsearch`:

- изменился `film_work` → обновляем `movies`
- изменился `genre` → обновляем связанные фильмы в `movies` и сам `genres`
- изменилась `person` → обновляем связанные фильмы в `movies` и сам `persons`

### Чекпоинты (State)

Состояние хранится в JSON-файле (`state/state.json`), смонтированном через Docker volume. Каждый пайплайн хранит свой чекпоинт — пару `{modified, id}` последней обработанной записи. При рестарте контейнера ETL продолжает с места остановки.

### Запуск индексов при старте

При запуске `main.py` проверяет наличие всех трёх индексов в Elasticsearch и создаёт отсутствующие с нужной схемой.


## Тесты

Тесты разделены на два типа:
- `tests/functional/` — функциональные тесты (требуют запущенных ES, Redis, API)
- `tests/resilience/` — тесты отказоустойчивости (без реального ES и Redis)

### Подготовка

Скопировать файл с переменными окружения:
```bash
cp tests/functional/.env.example tests/functional/.env
```

### Запуск через Makefile (рекомендуется)

```bash
make test-functional        # функциональные тесты (ES + Redis + FastAPI в docker)
make test-functional-empty  # тесты с пустым Elasticsearch
make test-resilience        # тесты отказоустойчивости (без реального ES/Redis)
make test-all               # все
```

Для `test-functional` и `test-functional-empty` контейнеры автоматически останавливаются и удаляются после завершения или при падении тестов. `test-resilience` контейнеры не поднимает — приложение запускается внутри pytest.

### Тесты отказоустойчивости

Находятся в `tests/resilience/`. Проверяют поведение API при недоступных внешних сервисах:

- `TestESUnavailable` — все list- и detail-эндпоинты возвращают 503
- `TestRedisUnavailable` — API возвращает 200, работая без кэша

Тесты запускаются без реального ES и Redis: приложение поднимается через `httpx.ASGITransport` внутри pytest, а клиенты мокируются на уровне методов.

Для локального запуска нужно установить зависимости из `src/requirements.txt` и `tests/resilience/requirements.txt`:
```bash
pip install -r src/requirements.txt -r tests/resilience/requirements.txt
pytest tests/resilience/ -v -c tests/resilience/pytest.ini
```

### Ручной запуск

#### Подготовка образа

```bash
cd tests/functional && docker compose build
```

#### Запуск инфраструктуры

```bash
docker compose up -d elasticsearch redis fastapi
```

#### Без дебаггера

```bash
docker compose run --rm tests
```

При изменении тестов пересборка образа не нужна — директория `tests/` примонтирована как volume и изменения подхватываются при следующем запуске.

#### С дебаггером (VS Code)

**1.** Запустить тесты в режиме ожидания:
```bash
docker compose run --rm --service-ports -e DEBUG=1 tests
```

**2.** Поставить брейкпойнт в тесте.

**3.** Подключиться к `localhost:5678` через debugpy в своей IDE.

#### Остановить инфраструктуру

```bash
docker compose down
```
