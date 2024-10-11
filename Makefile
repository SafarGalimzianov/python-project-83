PORT := 1624

i:
	poetry install

u:
	poetry update

b:
	poetry build

f:
	poetry run flask run --app page_analyzer run --port $(PORT)--debug

g:
	poetry run gunicorn --bind=localhost:$(PORT) page_analyzer:app

t:
	poetry run pytest

tv:
	poetry run pytest -v