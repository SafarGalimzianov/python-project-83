# Для log_execution_time
import logging
from time import time
from functools import wraps

from requests import Session
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from bleach import clean


REQUEST_TIMEOUT = 5


session = Session()


def get_current_date() -> str:  # Получение текущей даты
    # Возврат текущей даты в формате 'YYYY-MM-DD'
    return datetime.now().strftime('%Y-%m-%d')


# Запрос к странице по URL вида https://www.example.com
# Получение URL в виде строки и возвращение данных ответа в виде словаря
def make_request(url: str) -> dict:
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    status_code = response.status_code

    soup = BeautifulSoup(response.text, 'html.parser')
    h1, title, description = '', '', ''
    if soup.h1:
        h1 = soup.h1.string
    if soup.title:
        title = soup.title.string

    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag:
        description = meta_tag['content']

    return {
        'name': url,
        'status_code': status_code,
        'h1': h1,
        'title': title,
        'description': description,
    }


def sanitize_url_input(user_input):
    cleaned_url = clean(user_input.strip(), strip=True)
    parsed_url = urlparse(cleaned_url)

    if not parsed_url.scheme or \
        not parsed_url.netloc or \
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
    def decorated_function(*args, multiplier=1000, precision=2, **kwargs):
        start_time = time()
        logging.info(f'Starting {f.__name__}')

        result = f(*args, **kwargs)
        # time() дает время в секундах
        execution_time = round(multiplier * (time() - start_time), precision)
        logging.info(f'Finished {f.__name__} in {execution_time}ms')

        return result
    return decorated_function


def log_config(name):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s -%(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )

    return logging.getLogger(name)
