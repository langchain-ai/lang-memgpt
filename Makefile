.PHONY: tests lint format evals


evals:
	LANGCHAIN_TEST_CACHE=tests/evals/cassettes poetry run python -m pytest -p no:asyncio  --max-asyncio-tasks 4 tests/evals

lint:
	poetry run ruff check .
	poetry run mypy .

format:
	ruff check --select I --fix
	poetry run ruff format .
	poetry run ruff check . --fix

build:
	poetry build

publish:
	poetry publish --dry-run
