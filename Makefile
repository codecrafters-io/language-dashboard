lint:
	python -m black ./src || true
	python -m isort ./src --skip .history --skip .venv
	python -m flake8 --extend-ignore E501,E203 ./src || true
	# python -m mypy ./src --explicit-package-bases || true
	python -m mypy ./src --explicit-package-bases --strict || true
	python -m ruff check ./src || true

run:
	python -m src.main