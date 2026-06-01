.PHONY: test-functional test-functional-empty

ENV_FILE = tests/functional/.env

# Requires tests/functional/.env (copy from tests/functional/.env.example)
test-functional:
	@[ -f "$(ENV_FILE)" ] || { \
		echo "Error: $(ENV_FILE) not found."; \
		echo "Run: cp tests/functional/.env.example $(ENV_FILE)"; \
		exit 1; \
	}
	docker compose -f tests/functional/docker-compose.yml --env-file $(ENV_FILE) up \
		--build --abort-on-container-exit --exit-code-from tests; \
	docker compose -f tests/functional/docker-compose.yml --env-file $(ENV_FILE) down -v

# Runs tests with empty ES (no data fixtures loaded)
test-functional-empty:
	@[ -f "$(ENV_FILE)" ] || { \
		echo "Error: $(ENV_FILE) not found."; \
		echo "Run: cp tests/functional/.env.example $(ENV_FILE)"; \
		exit 1; \
	}
	docker compose -f tests/functional/docker-compose.yml --env-file $(ENV_FILE) \
		run --rm --entrypoint pytest tests \
		/app/tests/functional/src/empty_es \
		-c /app/tests/functional/pytest.ini -v; \
	docker compose -f tests/functional/docker-compose.yml --env-file $(ENV_FILE) down -v
