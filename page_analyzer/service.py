# Для log_execution_time
import logging
from time import time
from functools import wraps

# Для отправки HTTP-запросов (make_request())
import requests
# Для парсинга HTML-кода (make_request())
from bs4 import BeautifulSoup
# Для работы с датой (make_request())
from datetime import datetime
# Для парсинга URL (validate_and_fix_url())
from urllib.parse import urlparse, urlunparse
# Для очистки данных HTML от вредоносных элементов (sanitize_url_input())
import bleach


def get_current_date() -> str:  # Получение текущей даты
    # Возврат текущей даты в формате 'YYYY-MM-DD'
    return datetime.now().strftime('%Y-%m-%d')


# Запрос к странице по URL вида https://www.example.com
# Получение URL в виде строки и возвращение данных ответа в виде словаря
session = requests.Session()


def make_request(url: str, fix=True) -> dict:
    try:
        response = session.get(url, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        h1_content = soup.h1.string if (soup.h1 and soup.h1.string) else ''
        title_content = soup.title.string \
            if (soup.title and soup.title.string) else ''
        description_content = ''

        if soup.find('meta', attrs={'name': 'description'}):
            description_content = \
                soup.find('meta', attrs={'name': 'description'})['content']

        return {
            'name': url,
            'status_code': response.status_code,
            'h1': h1_content,
            'title': title_content,
            'description': description_content,
            'created_at': get_current_date()
        }
    except (requests.RequestException, requests.ConnectionError):
        return {'name': False, 'error': 'Connection error'}


def sanitize_url_input(user_input):
    cleaned_url = bleach.clean(user_input.strip(), strip=True)
    parsed_url = urlparse(cleaned_url)

    if not parsed_url.scheme or not parsed_url.netloc or \
            parsed_url.scheme not in ['http', 'https']:
        return None

    normalized_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        '',
        '',
        '',
        '',
    ))
    return normalized_url


def log_execution_time(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time()
        logging.info(f'Starting {f.__name__}')

        result = f(*args, **kwargs)

        execution_time = time() - start_time
        logging.info(f'Finished {f.__name__} in {execution_time}')

        return result
    return decorated_function
