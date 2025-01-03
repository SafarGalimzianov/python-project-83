PORT ?=10000

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
	poetry run pytest .

tv:
	poetry run pytest -v .

l:
	poetry run flake8 page_analyzer/app.py page_analyzer/app_repository.py


install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

start:
	poetry run gunicorn --timeout 60 -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

reinstall:
	python3 -m pip install --user dist/*.whl --force-reinstall

build:
	./build.sh