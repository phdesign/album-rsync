VENV_NAME       ?= .venv
ifdef OS
	PYTHON          ?= python
	VENV_ACTIVATE   ?= $(VENV_NAME)/Scripts/activate
else
	PYTHON          ?= python3
	VENV_ACTIVATE   ?= $(VENV_NAME)/bin/activate
endif

init:
	pip install -r requirements.txt

venv:
	test -d $(VENV_NAME) || $(PYTHON) -m venv $(VENV_NAME)
	source $(VENV_ACTIVATE); \
	pip install -r requirements.txt; \
	pip install -r tests/requirements.txt

lint:
	@source $(VENV_ACTIVATE); \
	pylint --exit-zero -f colorized {**,.}/*.py

test: lint
	@source $(VENV_ACTIVATE); \
	python setup.py test

clean:
	rm -rf .venv
	rm -rf .pytest_cache
	find . -iname "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

.PHONY: init venv lint test clean
