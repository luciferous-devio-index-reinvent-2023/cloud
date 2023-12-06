SHELL = /usr/bin/env bash -xeuo pipefail

black:
	poetry run black src/

isort:
	poetry run isort src/

lint:
	poetry run pyright src/

format: black isort lint

.PHONY: \
	black \
	isort \
	lint \
	format
