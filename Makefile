VENV_NAME ?= .venv
PYTHON ?= python

get_python_version = $(word 2,$(subst ., ,$(shell $(1) --version 2>&1)))
ifneq ($(call get_python_version,$(PYTHON)), 3)
    PYTHON = python3
endif
ifneq ($(call get_python_version,$(PYTHON)), 3)
    $(error "No supported python found! Requires python v3.6+")
endif

ifdef OS
    VENV_ACTIVATE ?= $(VENV_NAME)/Scripts/activate
else
    VENV_ACTIVATE ?= $(VENV_NAME)/bin/activate
endif

init:
	pip install -r requirements.txt

venv:
	test -d $(VENV_NAME) || $(PYTHON) -m venv $(VENV_NAME)
	source $(VENV_ACTIVATE); \
	pip install -r requirements.txt; \
	pip install -r tests/requirements.txt

lint:
	@test -d $(VENV_NAME) && source $(VENV_ACTIVATE); \
	pylint --exit-zero -f colorized {**,.}/*.py

test: lint
	@test -d $(VENV_NAME) && source $(VENV_ACTIVATE); \
	python setup.py test

clean:
	rm -rf .venv
	rm -rf .pytest_cache
	find . -iname "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

deploy: test
	$(PYTHON) setup.py sdist upload

.PHONY: init venv lint test clean deploy
.DEFAULT: test
