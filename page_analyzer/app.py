from functools import wraps

from os import getenv

from flask import (
    abort,
    get_flashed_messages,
    flash,
    Flask,
    redirect,
    render_template,
    request,
    url_for,
)

from requests import RequestException, ConnectionError

from dotenv import load_dotenv

from page_analyzer.app_repository import AppRepository

from page_analyzer.service import (
    make_request,
    sanitize_url_input,
    get_current_date,
    log_execution_time,
    log_config
)

from page_analyzer.db_pool import ConnectionPool


load_dotenv()

# Инстанцирование веб-приложения
app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )
app.jinja_env.trim_blocks = True  # Удаление пробелов в шаблоне
app.jinja_env.lstrip_blocks = True  # Удаление пробелов в шаблоне
app.jinja_env.autoescape = True  # Экранирование HTML-символов


# Установка заголовков безопасности
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


# Получение URL базы данных из переменных окружения
app.config['DATABASE_URL'] = getenv('DATABASE_URL')

# Инициализация соединения с базой данных
pool = ConnectionPool(getenv('DATABASE_URL'))
pool.init_pool()
repo = AppRepository(pool)


# Добавление flash сообщений
def add_flashed_messages(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        messages = get_flashed_messages(with_categories=True)
        return f(*args, messages=messages, **kwargs)
    return decorated_function


# Настройка логера
logger = log_config(__name__)


# Страница поиска
@app.get('/')
@log_execution_time
@add_flashed_messages
def search(messages=None):
    return render_template('main/search.html', messages=messages)


# Отображение списка URL
@app.get('/urls')
@log_execution_time
@add_flashed_messages
def get_urls(messages=None):
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Число URL на странице

    urls, total = repo.get_urls_paginated(page, per_page)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'main/urls.html',
        urls=urls,
        current_page=page,
        total_pages=total_pages,
        max=max,
        min=min,
        messages=messages,
    )


# Страница добавления URL
@app.post('/urls')
@log_execution_time
def add_url():
    url = sanitize_url_input(request.form.to_dict()['url'])

    if not url:
        flash('Некорректный URL', 'danger')
        '''
        Не можем использовать redirect,
        так как при redirect status code должен быть 3**
        а по тестам требуется 422.
        В результате у некоторых браузеров возникает ошибка
        и не делают автоматический redirect
        '''
        return render_template('main/search.html'), 422

    url_id = repo.get_url_id_by_name(url)
    if url_id:
        flash('Страница уже существует', 'info')
    else:
        url_id = repo.add_url(url, get_current_date())
        flash('Страница успешно добавлена', 'success')

    return redirect(url_for('get_url', url_id=url_id['id']))


# Страница с информацией об URL по уникальному id URL
@app.get('/urls/<int:url_id>')
@log_execution_time
@add_flashed_messages
def get_url(url_id, messages=None):
    url_info = repo.get_url_info(url_id)
    if not url_info:
        abort(404)
    checks = repo.get_url_checks(url_id)

    return render_template(
        'main/url_info.html',
        url_id=url_id,
        url_info=url_info,
        checks=checks,
        messages=messages,
    )


# Проверка URL производится на странице с информацией о сайте
@app.post('/urls/<int:url_id>')
@log_execution_time
def check_url(url_id: int):
    url = repo.get_url_name_by_id(url_id)
    if not url:
        flash('URL не найден', 'error')
        abort(404)

    try:
        data = make_request(url['name'])
    except (RequestException, ConnectionError) as e:
        flash(f'Произошла ошибка при проверке: {e}', 'error')
    else:
        repo.check_url(data, get_current_date())
        flash('Страница успешно проверена', 'success')

    return redirect(url_for('get_url', url_id=url_id))


# Обработка HTTP ошибок
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(422)
@app.errorhandler(500)
def handle_error(e):
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
