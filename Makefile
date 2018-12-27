init:
	pip install -r requirements.txt

lint:
	pylint {**,.}/*.py

test:
	python setup.py test

publish:
	python setup.py sdist upload

.PHONY: init lint test publish
