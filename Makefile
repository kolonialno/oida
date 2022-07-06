all : black mypy isort flake8 pytest

.PHONY: black
black:
	black --check oida tests bin/*

.PHONY: mypy
mypy:
	mypy
	mypy bin/create-github-release

.PHONY: isort
isort:
	isort --check-only oida tests bin/*

.PHONY: flake8
flake8:
	flake8 oida tests bin/*

.PHONY: pytest
pytest:
	pytest
