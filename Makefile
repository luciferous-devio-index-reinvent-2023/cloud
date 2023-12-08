SHELL = /usr/bin/env bash -xeuo pipefail

black:
	poetry run black src/

isort:
	poetry run isort src/

pyright:
	PYTHONPATH=src/layers/common/python \
	poetry run pyright src/

terraform-fmt-root:
	terraform fmt

terraform-fmt-module-common:
	cd terraform_modules/common && \
	terraform fmt

terraform-fmt-module-lambda-function-basic:
	cd terraform_modules/lambda_function_basic && \
	terraform fmt

terraform-fmt-module-lambda-function:
	cd terraform_modules/lambda_function && \
	terraform fmt

terraform-fmt: \
	terraform-fmt-root \
	terraform-fmt-module-common \
	terraform-fmt-module-lambda-function-basic \
	terraform-fmt-module-lambda-function

format: \
	black \
	isort \
	pyright \
	terraform-fmt

.PHONY: \
	black \
	isort \
	pyright \
	terraform-fmt-root \
	terraform-fmt-module-common \
	terraform-fmt-module-lambda-function-basic \
	terraform-fmt-module-lambda-function \
	terraform-fmt \
	format
