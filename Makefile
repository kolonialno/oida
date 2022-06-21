all : black mypy isort flake8 pytest

.PHONY: black
black:
	black --check oida tests

.PHONY: mypy
mypy:
	mypy --show-error-codes oida tests

.PHONY: isort
isort:
	isort --check-only oida tests

.PHONY: flake8
flake8:
	flake8 oida tests

.PHONY: pytest
pytest:
	pytest
