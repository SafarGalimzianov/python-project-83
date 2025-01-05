from functools import wraps  # Для декоратора

# Для получения переменных окружения
from os import getenv
# Для работы с базой данных (app_repository.py)
import psycopg2
# Для создания веб-приложения
from flask import (
    abort,  # Вызов ошибки
    get_flashed_messages,  # Получение сообщений пользователю
    flash,  # Отображение сообщения пользователю
    Flask,  # Создание экземпляра веб-приложения
    redirect,  # Редирект на другую страницу
    render_template,  # Рендеринг шаблона
    request,  # Получение ответа от пользователя
    url_for,  # Получение пути по имени функции
)

# from urllib.parse import urlparse  # Для парсинга URL

# Для загрузки переменных окружения из файла .env
from dotenv import load_dotenv

# Класс AppRepository из app_repository.py для работы с базой данных
from page_analyzer.app_repository import AppRepository

# Для выполнения запроса к URL:
# исправление неверный URL при возникновении ошибок и получение данных ответа
from page_analyzer.service import \
    make_request, sanitize_url_input, get_current_date

load_dotenv()  # Загрузка переменных окружения из файла .env

# Инстанцирование веб-приложения с именем __name__
# Таким образом Flask знает, где искать шаблоны и статические файлы
app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )
app.jinja_env.trim_blocks = True  # Удаление пробелов в шаблоне
app.jinja_env.lstrip_blocks = True  # Удаление пробелов в шаблоне
app.jinja_env.autoescape = True  # Экранирование HTML-символов


# Установка заголовков безопасности
# In app.py, update the CSP header to include FontAwesome CDN
@app.after_request
def add_csp_header(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self';"
    )
    return response


# Получение ключа сессии и URL базы данных из переменных окружения
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['DATABASE_URL'] = getenv('DATABASE_URL')
app.config['PORT'] = getenv('PORT')

'''
def create_tables():
    conn = psycopg2.connect(app.config['DATABASE_URL'])
    cur = conn.cursor()
    with conn:
        with open('database.sql') as f:
            cur.execute(f.read())
'''


def with_db_connection(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        conn = None
        try:
            conn = psycopg2.connect(getenv('DATABASE_URL'))
            # Pass connection to global repo instance
            global repo
            repo = AppRepository(conn)
            return f(*args, **kwargs)
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            flash('Database error: ' + str(e), 'error')
            abort(500)
        finally:
            if conn:
                conn.close()
    return decorated_function


# Отображение главной страницы
@app.get('/')  # Главная страница
@with_db_connection
def search():  # Форма поиска, поэтому search
    # Получение сообщений пользователю
    messages = get_flashed_messages(with_categories=True)
    return render_template('main/search.html', messages=messages)


# Добавление URL
@app.post('/urls')
@with_db_connection
def add_url():
    try:
        url = request.form.to_dict()['url']
        url = sanitize_url_input(url)

        if not url:
            flash('Некорректный URL', 'danger')
            return render_template('main/search.html'), 422

        if repo.in_db(url):
            flash('Страница уже существует', 'info')
            url_id = repo.get_url_by_name(url)['id']
            return redirect(url_for('get_url', url_id=url_id))

        try:
            url_id = repo.add_url(url, get_current_date())['id']
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('get_url', url_id=url_id))
        except Exception:
            flash('Произошла ошибка при добавлении страницы', 'danger')
            return render_template('main/search.html'), 422

    except Exception:
        flash('Некорректный URL', 'danger')
        return render_template('main/search.html'), 422


# Отображение информации о сайте
# Каждая страница имеет уникальный URL, поэтому url_id
@app.get('/urls/<int:url_id>')
@with_db_connection
# Получение id URL, который совпадает с идентификатором URL в базе данных
def get_url(url_id):
    url_info = repo.get_url_info(url_id)  # Поиск информации о URL по url_id
    if not url_info:  # Если URL не найден в базе данных
        abort(404)  # Вызов ошибки 404
    # Получение информации о проверках URL
    checks = repo.get_url_checks(url_id)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'main/url_info.html',
        url_id=url_id,
        name=url_info['name'],
        created_at=url_info['created_at'],
        checks=checks,
        messages=messages,
    )


# Проверка URL производится на странице с информацией о сайте
@app.post('/urls/<int:url_id>')
@with_db_connection
def check_url(url_id: int):
    url = repo.get_url_address(url_id)
    if not url:
        flash('URL не найден', 'error')
        abort(404)

    try:
        data = make_request(url['name'])
        if not data['name']:
            flash('Произошла ошибка при проверке', 'error')
            return redirect(url_for('get_url', url_id=url_id))

        repo.check_url(data)
        flash('Страница успешно проверена', 'success')
        return redirect(url_for('get_url', url_id=url_id))
    except Exception:
        flash('Произошла ошибка при проверке', 'error')
        return redirect(url_for('get_url', url_id=url_id))


# Отображение списка URL
@app.get('/urls')
@with_db_connection
def get_urls():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Число URL на странице

    urls, total = repo.get_urls_paginated(page, per_page)
    total_pages = (total + per_page - 1) // per_page

    messages = get_flashed_messages(with_categories=True)

    return render_template(
        'main/urls.html',
        urls=urls,
        current_page=page,
        total_pages=total_pages,
        max=max,
        min=min,
        messages=messages,
    )


# Обработка HTTP ошибок
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(422)
@app.errorhandler(500)
def handle_error(e):
    # Коды ошибок и сообщения
    error_messages = {
        400: "Неверный запрос",
        404: "Такой страницы не существует",
        422: "Неверный URL",
        500: "Внутренняя ошибка сервера"
    }

    # Получение кода ошибки
    error_code = e.code if hasattr(e, 'code') else 500
    error_msg = error_messages.get(error_code, "Unknown Error")

    return render_template(
        'errors/error.html',
        error_code=error_code,
        error_message=error_msg
    ), error_code
