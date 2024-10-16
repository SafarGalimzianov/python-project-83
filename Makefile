PORT ?=1624

i:
	poetry install

u:
	poetry update

b:
	poetry build

f:
	poetry run flask --app page_analyzer.app run --port $(PORT) --debug

g:
	poetry run gunicorn --bind=localhost:$(PORT) page_analyzer.app:app

t:
	poetry run pytest

tv:
	poetry run pytest -v

l:
	poetry run flake8 page_analyzer/app.py page_analyzer/app_repository.py