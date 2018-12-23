init:
	pip install -r requirements.txt

lint:
	pylint {**,.}/*.py

test:
	python setup.py test

.PHONY: init lint test
