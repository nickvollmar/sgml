.PHONY: all
all: test

.PHONY: test
test:
	python -m unittest discover -s tests
