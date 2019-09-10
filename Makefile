.PHONY: all
all: test

# https://www.hergertarian.com/cheat-sheet-publishing-a-python-package
.PHONY: dist
dist:
	python3 -m pip install --user --upgrade setuptools wheel
	python3 setup.py sdist bdist_wheel

venv := .virtualenv

$(venv): $(venv)/bin/activate

$(venv)/bin/activate: requirements.txt
	test -d $(venv) || python3 -m venv $(venv)
	. $(venv)/bin/activate && python -m pip install -Ur requirements.txt
	touch $(venv)/bin/activate

test: $(venv)
	. $(venv)/bin/activate && python -m unittest

clean:
	rm -rf $(venv)
	find -iname "*.pyc" -delete
