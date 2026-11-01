install:
	uv sync

lint:
	uv run ruff check .

run:
	uv run database

build:
	uv build
