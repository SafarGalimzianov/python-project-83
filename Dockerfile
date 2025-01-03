# Использование сжатой версии образа python для снижения размера образа
FROM python:3.12-slim

# Создание обычного пользователя для использования вместо root для большей безопасности
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Создание домашней директории для пользователя и установка прав на нее
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

# Создание рабочей директории для приложения
# Docker будет использовать эту директорию
WORKDIR /app

# Добавление пути к исполняемым файлам в переменную окружения PATH
ENV PATH="$PATH:/home/appuser/.local/bin"

# Обновление пакетов, затем установка  make gcc, libpq-dev и postgresql-clien для postgresql. Удаление кэша, созданного apt-get uodate
# apt-get лучше справляется со скриптами и автоматическими установками, чем apt
RUN apt-get update && apt-get install -yq make build-essential gcc libpq-dev postgresql-client && apt-get clean && rm -rf /var/lib/apt/lists/*

# Переключение с root на обычного пользователя
USER appuser

# Установка poetry (без root, поэтому только в рамках домашней директории)
RUN pip install poetry

# Копирование конфигурационных файлов для установки зависимостей
COPY pyproject.toml poetry.lock ./

# Установка только зависимостей (без установки самого приложения)
# Это позволяет использовать кэширование слоев Docker, что ускоряет сборку
RUN poetry install --no-root

# Копирование образа из директории хоста в рабочую директорию /app
COPY . .

# Установках переменных среды для запуска приложения при помощи Flask
ENV FLASK_APP=page_analyzer.app:app
ENV FLASK_RUN_HOST=0.0.0.0

# Порт не устанавливается, так как используется Render
# Render самостоятельно назначает порт (указывается в настройках среды в проекте на Render)

# Подключение к БД с загрузкой настроек (таблицы, индексы и прочее)
# Запуск приложения
CMD ["sh", "-c", "psql -a -d $DATABASE_URL -f database.sql && poetry run gunicorn --timeout 60 -w 5 --bind=0.0.0.0:$PORT page_analyzer.app:app"]
