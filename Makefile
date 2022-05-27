PACKAGE = hasher

PYVERS = 3.7 3.8 3.9 3.10
PYVER  = $(firstword $(PYVERS))

VIRTUAL_ENV := $(lastword $(shell poetry env use python$(PYVER)))
SITE_PACKAGES = $(VIRTUAL_ENV)/lib/python$(PYVER)/site-packages

PYTEST_FLAGS = -vv

.PHONY: all
all: lint test

.PHONY: format fmt
format fmt: venv
	poetry run isort src/ tests/
	poetry run black src/ tests/

.PHONY: lint
lint: venv
	poetry run flake8 src/ tests/
	poetry run isort --check --diff src/ tests/
	poetry run black --check --diff src/ tests/
	poetry run mypy src/

.PHONY: test
test:
	poetry run pytest $(PYTEST_FLAGS) tests/

.PHONY: coverage
coverage: PYTEST_FLAGS += --cov --cov-report=term-missing
coverage: test


.PHONY: venv
venv: $(SITE_PACKAGES)/$(PACKAGE).pth

$(SITE_PACKAGES)/$(PACKAGE).pth: poetry.lock
	poetry install

poetry.lock: pyproject.toml
	poetry lock
