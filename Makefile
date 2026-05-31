.PHONY: install install-dev lint test build clean check

install:
	python -m pip install -e .

install-dev:
	python -m pip install -e ".[dev,all]"

lint:
	ruff check .
	ruff format --check .

test:
	pytest

build:
	python -m build

check: lint test build

clean:
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
