PACKAGE = hasher

PYVERS = 3.10 3.11 3.12 3.13 3.14
PYVER  = $(firstword $(PYVERS))
UV_PYTHON = $(PYVER)
export UV_PYTHON

VIRTUAL_ENV := .venv
SITE_PACKAGES = $(VIRTUAL_ENV)/lib/python$(PYVER)/site-packages

PYTEST_FLAGS = -vv

.PHONY: all
all: lint test

.PHONY: clean
clean:
	rm -rf $(VIRTUAL_ENV) dist/ .mypy_cache/ .pytest_cache/ .ruff_cache/
	find . -name '__pycache__' -type d -exec rm -rf '{}' +

.PHONY: format fmt
format fmt: venv
	uv run ruff check --select I --fix
	uv run ruff format .

.PHONY: lint
lint: venv
	uv run ruff check
	uv run mypy src/

.PHONY: test
test:
	uv run pytest $(PYTEST_FLAGS) tests/

.PHONY: coverage
coverage: PYTEST_FLAGS += --cov --cov-report=term-missing
coverage: test


.PHONY: venv
venv: $(SITE_PACKAGES)/$(PACKAGE).pth

$(SITE_PACKAGES)/$(PACKAGE).pth: uv.lock | $(VIRTUAL_ENV)/bin/activate 
	uv sync
	touch $@

$(VIRTUAL_ENV)/bin/activate:
	uv venv

uv.lock: pyproject.toml
	uv lock
	@touch $@
