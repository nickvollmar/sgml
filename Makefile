current_dir := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.PHONY: all
all: test

# https://www.hergertarian.com/cheat-sheet-publishing-a-python-package
.PHONY: dist
dist:
	python3 -m pip install --user --upgrade setuptools wheel
	python3 setup.py sdist bdist_wheel

.PHONY: test
test:
	python3 -m unittest

.PHONY: clean
clean:
	find $(current_dir) \
	  '(' '(' -type f -name '*.pyc' ')' -or '(' -type d -name __pycache__ ')' ')' \
	  -delete
