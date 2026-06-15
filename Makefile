test:
	uv run pytest -vvs tests/

lint: ## lint the source code
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

fmt: ## format the source code with ruff
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
