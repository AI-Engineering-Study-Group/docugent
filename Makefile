compose_service = backend

add-package:
	@poetry add $(pkg)
	@poetry install
	@docker compose build

add-dev-package:
	@poetry add --group dev $(pkg)
	@poetry install
	@docker compose build

up:
	@docker compose up

bash:
	@docker compose run --rm ${compose_service} bash

build:
	@docker compose build

build-up:
	@docker compose up --build

down:
	@docker compose down --remove-orphans

format:
	@docker compose run --rm ${compose_service} poetry run ruff format ./app
	@docker compose run --rm ${compose_service} poetry run ruff check ./app --fix --select I

install:
	@poetry install

lint:
	@docker compose run --rm ${compose_service} poetry run ruff check .
	@docker compose run --rm ${compose_service} poetry run ruff format --check .

lint-full:
	@docker compose run --rm ${compose_service} poetry run ruff check .
	@docker compose run --rm ${compose_service} poetry run ruff format --check .
	@docker compose run --rm ${compose_service} poetry run mypy .

run-command:
	@docker compose run --rm ${compose_service} $(command)

shell:
	@docker compose run --rm ${compose_service} python manage.py shell

stop:
	@docker compose stop

test:
	@docker compose run --rm ${compose_service} poetry run pytest .

testcase:
	@docker compose run --rm ${compose_service} poetry run pytest $(t)

up-d:
	@docker compose up -d
