# Добавление библиотеки os для получения переменных окружения ('SECRET_KEY', 'DATABASE_URL')
import os
# Добавление библиотеки psycopg для работы с базой данных (app_repository.py)
import psycopg
# Добавление библиотеки requests для отправки HTTP-запросов (make_request())
import requests
# Добавление библиотеки BeautifulSoup для парсинга HTML-кода (make_request())
from bs4 import BeautifulSoup
# Добавление библиотеки datetime для работы с датой (make_request())
from datetime import datetime
# Добавление библиотеки Flask для создания веб-приложения
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

import validators  # Проверка URL на валидность
from urllib.parse import urlparse, urlunparse  # Парсинг и анпарсинг URL
import re  # Регулярные выражения для получения домена из URL
import bleach  # Очистка HTML-кода от вредоносных элементов

from dotenv import load_dotenv  # Добавление функции для загрузки переменных окружения из файла .env

# Добавление класса AppRepository из файла app_repository.py для работы с базой данных
from page_analyzer.app_repository import AppRepository

load_dotenv()  # Загрузка переменных окружения из файла .env

# Инстанцирование веб-приложения с именем __name__
# Таким образом Flask знает, где искать шаблоны и статические файлы
app = Flask(__name__, template_folder='../templates')  # Flask будет искать шаблоны в папке выше и затем в templates/
app.jinja_env.trim_blocks = True  # Удаление пробелов в шаблоне
app.jinja_env.lstrip_blocks = True  # Удаление пробелов в шаблоне
app.jinja_env.autoescape = True  # Экранирование HTML-символов


# Установка заголовков безопасности
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self';"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Получение ключа сессии
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')  # Получение URL базы данных

conn = psycopg.connect(app.config['DATABASE_URL'])  # Соединение с базой данных

repo = AppRepository(conn)  # Инстанцирование класса AppRepository


def get_current_date() -> str:  # Получение текущей даты
    return datetime.now().strftime('%Y-%m-%d')  # Возврат текущей даты в формате 'YYYY-MM-DD'


# Форматирование даты
def format_date(date: str) -> str:
    possible_formats = [
        ('RFC 1123', '%a, %d %b %Y %H:%M:%S GMT'),  # Стандартный формат
        ('RFC 850', '%A, %d-%b-%y %H:%M:%S %Z'),  # Устаревший стандартный формат
        ('ANSI C', '%a %b %d %H:%M:%S %Y'),  # Нестандартный формат
        ('ISO 8601', '%Y-%m-%dT%H:%M:%S%z'),  # Нестандартный формат
    ]
    for possible_format in possible_formats:  # Перебор форматов даты
        # Преобразование даты в формат 'YYYY-MM-DD' для базы данных с колонкой формата DATE
        try:
            # Преобразование даты в объект datetime
            result = datetime.strptime(date, possible_format[1]).date()
            result = result.strftime('%Y-%m-%d')  # Приведение даты к формату 'YYYY-MM-DD'
            return result  # Возврат даты
        except ValueError:  # При возникновении ошибки при преобразовании даты
            continue  # Переход к следующему формату
    return get_current_date()  # Текущая дата


# Запрос к странице по URL вида https://www.example.com
# Получение URL в виде строки и возвращение данных ответа в виде словаря
def make_request(url: str, fix=True) -> dict:
    if fix:
        fixed_url = validate_and_fix_url(url)  # Проверка URL на доступность и исправление ошибки в URL при недоступности
        if not fixed_url:
            return {'url': False}  # Возврат False при недоступности URL
        url = fixed_url
    try:
        response = requests.get(url)  # Получение ответа
    except requests.ConnectionError: # Если не удается получить ответ
        return {'url': False}  # Возврат False при ошибке соединения
    response_code = response.status_code  # Получение кода ответа

    soup = BeautifulSoup(response.text, 'html.parser')  # Получение остальных данных ответа
    h1_content = soup.h1.string if (soup.h1 and soup.h1.string) else ''  # Получение данных шапки
    title_content = soup.title.string if (soup.title and soup.title.string)  else ''  # Получение данных заголовка

    description_content = ''  # Значениие по умолчанию для метатега 'description'
    if soup.find('meta', attrs={'name': 'description'}):  # Если у страницы есть метатег 'description'
        # Получение данных метатега 'description'
        description_content = soup.find('meta', attrs={'name': 'description'})['content']
    date_header = response.headers.get('Date')
    check_date = format_date(date_header) if date_header else get_current_date()  # Получение даты запроса

    # Возврат данных ответа в виде словаря
    # Ни одно из значений не будет None,
    # поэтому проверки на добавление NULL значений в базу данных не требуется
    return {
        'url': url,
        'response_code': response_code,
        'h1': h1_content,
        'title': title_content,
        'description': description_content,
        'check_date': check_date
    }


# Проверка URL на доступность
def validate_and_fix_url(url: str) -> bool:  # Получение URL в виде строки и возвращение True или False
    funcs = {
        'is_reachable': _is_reachable,  # Проверка доступности URL
        'correct_scheme': _correct_scheme,  # Проверка схемы URL
        'extract_domain': _extract_domain  # Извлечение домена из URL
    }
    # Проверка синтаксиса URL
    if funcs['is_reachable'](url):
        return url  # Возврат исходного URL

    # Попытка исправить схему URL
    valid_schemes = ['https', 'http']  # Список валидных схем
    parsed_url = urlparse(url)  # Парсинг URL

    if parsed_url.scheme not in valid_schemes:  # Если схема URL не в списке валидных схем
        for scheme in valid_schemes:  # Перебор схем
            corrected_url = funcs['correct_scheme'](parsed_url, scheme)  # Проверка схемы URL
            if funcs['is_reachable'](corrected_url):  # Если URL доступен
                return corrected_url  # Возврат исправленного URL

    # Попытка исправить домен URl
    domain_info = funcs['extract_domain'](url)
    if not domain_info:
        return False  # Возврат False при недоступности URL
    domain, path = domain_info
    parsed_url = urlparse(url)
    for scheme in valid_schemes:
        if funcs['is_reachable'](urlunparse(parsed_url._replace(scheme=scheme, netloc=domain, path=''))):
            if path and funcs['is_reachable'](urlunparse(parsed_url._replace(scheme=scheme, netloc=domain, path=path))):
                return urlunparse(parsed_url._replace(scheme=scheme, netloc=domain, path=path))
            return urlunparse(parsed_url._replace(scheme=scheme, netloc=domain, path=''))

    # Попытка исправить домен URl
    domain_info = funcs['extract_domain'](url)
    if not domain_info:
        return False  # Возврат False при недоступности URL
    domain, path = domain_info
    parsed_url = urlparse(url)
    for scheme in valid_schemes:
        if funcs['is_reachable'](urlunparse(parsed_url._replace(scheme=scheme, netloc=domain, path=''))):
            if path and funcs['is_reachable'](urlunparse(parsed_url._replace(scheme=scheme, netloc=domain, path=path))):
                return urlunparse(parsed_url._replace(scheme=scheme, netloc=domain, path=path))
            return urlunparse(parsed_url._replace(scheme=scheme, netloc=domain, path=''))


def _correct_scheme(parsed_url: str, scheme: str) -> str:  # Получение URL в виде строки и возвращение схемы
    if parsed_url.scheme != scheme:  # Если URL не содержит схему
        '''
        Пример:
        url = 'https://www.google.com'
        parsed_url = ('HTML', 'www.google.com', '', '', '', '')
        parsed_url.scheme = ('www.google.com', '', '', '', '')
        '''
        return urlunparse(parsed_url._replace(scheme=scheme))  # Возврат URL с валидной схемой
    return urlunparse(parsed_url)  # Возврат исходного URL


def _is_reachable(url: str) -> bool:  # Получение URL в виде строки и возвращение True или False
    # Список валидных кодов ответа
    valid_responses = [
        200,  # Успешный запрос
        301,  # Перенаправление
        302,  # Перенаправление
    ]
    try:
        response = requests.get(url, timeout=20, allow_redirects=True)  # Получение ответа
        return response.status_code in valid_responses  # При успешном ответе возвращается True
    except requests.RequestException:  # Если возкает ошибка при запросе
        return False  # При ошибке возвращается False


def _extract_domain(url: str) -> str:  # Получение URL в виде строки и возвращение домена
    # Создание паттерна для поиска домена и пути в URL
    pattern = re.compile(
        r'^(?:http[s]?://)?'  # Получение схемы
        r'(?P<domain>[^:/\s]+)'  # Получение домена
        r'(?:[:]\d+)?'  # Получение порта
        r'(?P<path>/[^\s]*)?'  # Получение пути
    )

    match = pattern.match(url)  # Поиск совпадений
    if match:  # Если есть хотя бы одно совпадение
        domain = match.group('domain')
        path = match.group('path') or ''
        return domain, path  # Возврат домена и пути
    return None  # Возврат None при отсутствии совпадений


def sanitize_url_input(user_input):  # Очистка данных от вредоносных элементов
    return bleach.clean(user_input, strip=True)  # Возврат очищенных данных


# Отображение главной страницы
@app.get('/')  # Главная страница
def search():  # Форма поиска, поэтому search
    messages = get_flashed_messages(with_categories=True)  # Получение сообщений пользователю
    return render_template('main/search.html', messages=messages)


# Добавление URL
@app.post('/')  # Форма поиска находится на главной странице
def add_url():  # Заполнение формы добавляет URL в базу данных, поэтому add_url
    url = request.form.to_dict()['url']  # Получение URL из формы
    url = sanitize_url_input(url)  # Очистка URL от вредоносных элементов
    url = make_request(url)['url']  # Получение конечного (после исправлений и редиректов) URL из ответа
    if not url:  # Если URL недоступен
        flash('URL неверный', 'error')  # Оповещение пользователя об ошибке
        return redirect(url_for('search'))  # Возврат на главную страницу

    # Если URL доступен, то URl добавляется в базу данных
    url_id = repo.add_url(url, get_current_date())['id']  # Добавление URL в базу данных
    return redirect(url_for('get_url', url_id=url_id))  # Редирект на страницу с информацией об URL


# Отображение информации о сайте
@app.get('/url/<int:url_id>')  # Каждая страница имеет уникальный URL, поэтому url_id
def get_url(url_id):  # Получение id URL, который совпадает с идентификатором URL в базе данных
    url_info = repo.get_url_info(url_id)  # Поиск информации о URL по url_id
    if not url_info:  # Если URL не найден в базе данных
        abort(404)  # Вызов ошибки 404
    checks = repo.get_url_checks(url_id)  # Получение информации о проверках URL
    checks.reverse()  # Переворачивание списка проверок для отображения в порядке убывания даты
    return render_template(
        'main/url_info.html',
        url_id=url_id,
        url_info=url_info,
        checks=checks
    )


# Проверка URL
@app.post('/url/<int:url_id>')  # Проверка URL производится на странице с информацией о сайте
def check_url(url_id: int):  # Проверка URL, поэтому check_url
    url = repo.get_url_address(url_id)['url']  # Получение информации о URL по url_id
    if not url:  # Если прошедший при добавлении в базу данных URL больше не доступен
        flash('URL больше не доступен', 'error')  # Предложение пользователю удалить URL
        abort(404)  # Вызов ошибки 404
    data = make_request(url)  # Получение данных ответа
    repo.check_url(data)  # Добавление данных проверки URL в базу данных
    return redirect(url_for('get_url', url_id=url_id))  # Перенаправление на страницу проверенного URL


# Отображение списка URL
@app.get('/urls')  # Для выводы списка всех добавленных URL используется отдельная страница
def get_urls():  # Получение списка URL, поэтому get_urls
    urls = repo.get_urls()  # Получение списка URL из базы данных
    return render_template('main/urls.html', urls=urls)  # Отображение списка URL

# Обработка HTTP ошибок
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(e):
    # Коды ошибок и сообщения
    error_messages = {
        400: "Неверный запрос",
        404: "Такой страницы не существует",
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
