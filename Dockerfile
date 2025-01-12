FROM python:3.12-slim

RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

WORKDIR /app

ENV PATH="$PATH:/home/appuser/.local/bin"

RUN apt-get update && apt-get install -yq make build-essential gcc libpq-dev postgresql-client && apt-get clean && rm -rf /var/lib/apt/lists/*

USER appuser

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY . .

ENV FLASK_APP=page_analyzer.app:app
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["sh", "-c", "psql -a -d $DATABASE_URL -f database.sql && poetry run gunicorn --timeout 60 -w 5 -b 0.0.0.0:$PORT page_analyzer.app:app"]
