BASE_PYTHON ?= python
VENV ?= venv
TEST_PATH ?= tests
PYTEST_ARGS ?= -v

ifeq ($(OS),Windows_NT)
VENV_PYTHON := $(VENV)/Scripts/python.exe
else
VENV_PYTHON := $(VENV)/bin/python
endif

PYTHON ?= $(VENV_PYTHON)

CODE_DIRS := src tests
FIXTURE_DIR := tests/fixtures
UNIT_TEST_ARGS := --ignore=tests/e2e

.DEFAULT_GOAL := help

.PHONY: help venv install install-dev format format-check lint typecheck quality \
	test test-unit test-e2e coverage check build check-dist package clean

help: ## Show available targets and configurable variables
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target> [BASE_PYTHON=python] [VENV=venv] [PYTHON=<venv-python>] [TEST_PATH=tests] [PYTEST_ARGS=\"-v\"]\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: $(VENV_PYTHON) ## Create the project virtual environment

$(VENV_PYTHON):
	$(BASE_PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip

install: venv ## Install the package in editable mode
	$(PYTHON) -m pip install -e .

install-dev: venv ## Install the package and development dependencies in editable mode
	$(PYTHON) -m pip install -e ".[dev]"

format: ## Format source code and tests with Black and isort
	$(PYTHON) -m black --extend-exclude '(^|/)tests/fixtures/' $(CODE_DIRS)
	$(PYTHON) -m isort --skip $(FIXTURE_DIR) $(CODE_DIRS)

format-check: ## Check formatting without changing files
	$(PYTHON) -m black --check --extend-exclude '(^|/)tests/fixtures/' $(CODE_DIRS)
	$(PYTHON) -m isort --check-only --skip $(FIXTURE_DIR) $(CODE_DIRS)

lint: ## Lint source code and tests with Flake8
	$(PYTHON) -m flake8 --exclude=$(FIXTURE_DIR) $(CODE_DIRS)

typecheck: ## Type-check the package with mypy
	$(PYTHON) -m mypy src

quality: format-check lint typecheck ## Run all non-mutating code-quality checks

test: ## Run all tests; override TEST_PATH or PYTEST_ARGS as needed
	$(PYTHON) -m pytest $(TEST_PATH) $(PYTEST_ARGS)

test-unit: ## Run tests that do not require the PDFDancer API
	$(PYTHON) -m pytest tests $(UNIT_TEST_ARGS) $(PYTEST_ARGS)

test-e2e: ## Run API-dependent end-to-end tests
	$(PYTHON) -m pytest tests/e2e $(PYTEST_ARGS)

coverage: ## Run all tests and report package coverage
	$(PYTHON) -m pytest $(TEST_PATH) $(PYTEST_ARGS) --cov=pdfdancer --cov-report=term-missing

check: quality test-unit ## Run the local pre-commit checks

build: ## Build the wheel and source distribution
	$(PYTHON) -m build

check-dist: ## Validate existing distribution artifacts with Twine
	$(PYTHON) -m twine check dist/*

package: clean ## Clean, build, and validate distribution artifacts
	$(MAKE) build
	$(MAKE) check-dist

clean: ## Remove generated build, test, coverage, and Python cache artifacts
	$(RM) -r build dist .pytest_cache .mypy_cache .coverage htmlcov src/*.egg-info
	find src tests -type d -name __pycache__ -prune -exec $(RM) -r {} +
