# Для отправки HTTP-запросов (make_request())
import requests
# Для парсинга HTML-кода (make_request())
from bs4 import BeautifulSoup
# Для работы с датой (make_request())
from datetime import datetime
# Для парсинга URL (validate_and_fix_url())
from urllib.parse import urlparse, urlunparse
# Для работы с регулярными выражениями (extract_domain())
import re
# Для очистки данных HTML от вредоносных элементов (sanitize_url_input())
import bleach


def get_current_date() -> str:  # Получение текущей даты
    # Возврат текущей даты в формате 'YYYY-MM-DD'
    return datetime.now().strftime('%Y-%m-%d')


def format_date(date: str) -> str:  # Форматирование даты
    possible_formats = [
        ('RFC 1123', '%a, %d %b %Y %H:%M:%S GMT'),  # Стандарт
        ('RFC 850', '%A, %d-%b-%y %H:%M:%S %Z'),  # Устаревший стандарт
        ('ANSI C', '%a %b %d %H:%M:%S %Y'),  # Нестандартный формат
        ('ISO 8601', '%Y-%m-%dT%H:%M:%S%z'),  # Нестандартный формат
    ]
    for possible_format in possible_formats:  # Перебор форматов даты
        # Преобразование в формат 'YYYY-MM-DD' для БД с колонкой формата DATE
        try:
            # Преобразование даты в объект datetime
            result = datetime.strptime(date, possible_format[1]).date()
            # Приведение даты к формату 'YYYY-MM-DD'
            result = result.strftime('%Y-%m-%d')
            return result  # Возврат даты
        except ValueError:  # При возникновении ошибки при преобразовании даты
            continue  # Переход к следующему формату
    return get_current_date()  # Текущая дата


# Запрос к странице по URL вида https://www.example.com
# Получение URL в виде строки и возвращение данных ответа в виде словаря
session = requests.Session()

def make_request(url: str, fix=True) -> dict:
    try:
        response = session.get(url, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        h1_content = soup.h1.string if (soup.h1 and soup.h1.string) else ''
        title_content = soup.title.string if (soup.title and soup.title.string) else ''
        description_content = ''
        
        if soup.find('meta', attrs={'name': 'description'}):
            description_content = soup.find('meta', attrs={'name': 'description'})['content']
            
        return {
            'name': url,
            'status_code': response.status_code,
            'h1': h1_content,
            'title': title_content,
            'description': description_content,
            'created_at': get_current_date()
        }
    except (requests.RequestException, requests.ConnectionError, requests.Timeout):
        return {'name': False, 'error': 'Connection error'}

    '''
    if fix:
        pass
    '''
    if fix:
        # Проверка и исправление URL при недоступности
        fixed_url = validate_and_fix_url(url)
        if not fixed_url:
            return {'name': False, 'error': 'The URL is not reachable'}
        url = fixed_url
    '''
    try:
        response = session.get(url, timeout=5)  # Получение ответа
    except requests.ConnectionError:  # Если не удается получить ответ
        return {'name': False, 'error': 'Connection could not be established'}
    except requests.Timeout:  # Если время ожидания ответа истекло
        return {'name': False, 'error': 'Timeout'}  # Возврат описания ошибки
    except requests.RequestException as e:  # Если возникает ошибка при запросе
        return {'name': False, 'error': str(e)}  # Возврат описания ошибки

    response_code = response.status_code  # Получение кода ответа

    # Получение остальных данных ответа
    soup = BeautifulSoup(response.text, 'html.parser')
    h1_content = soup.h1.string \
        if (soup.h1 and soup.h1.string) else ''  # Получение данных шапки
    title_content = soup.title.string \
        if (soup.title and soup.title.string) else ''  # Получение заголовка

    # Значениие по умолчанию для метатега 'description'
    description_content = ''
    # Если у страницы есть метатег 'description'
    if soup.find('meta', attrs={'name': 'description'}):
        # Получение данных метатега 'description'
        description_content = \
            soup.find('meta', attrs={'name': 'description'})['content']
    date_header = response.headers.get('Date')
    # Получение даты запроса, в случае отсутсвия берется текущая дата
    check_date = format_date(date_header) \
        if date_header else get_current_date()

    # Возврат данных ответа в виде словаря
    # Ни одно из значений не будет None,
    # поэтому проверки на добавление NULL значений в базу данных не требуется
    return {
        'name': url,
        'status_code': response_code,
        'h1': h1_content,
        'title': title_content,
        'description': description_content,
        'created_at': check_date
    }
    '''

# Проверка URL на доступность
# Получение URL в виде строки и возвращение True или False
def validate_and_fix_url(url: str) -> bool:
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

    # Если схема URL не в списке валидных схем
    if parsed_url.scheme not in valid_schemes:
        for scheme in valid_schemes:  # Перебор схем
            corrected_url = funcs['correct_scheme'](parsed_url, scheme)
            if funcs['is_reachable'](corrected_url):  # Если URL стал доступен
                return corrected_url  # Возврат исправленного URL

    # Попытка исправить домен URl
    domain_info = funcs['extract_domain'](url)
    if not domain_info:
        return False  # Возврат False при недоступности URL
    domain, path = domain_info
    parsed_url = urlparse(url)
    for scheme in valid_schemes:
        if funcs['is_reachable'](urlunparse(parsed_url._replace(
                                                scheme=scheme,
                                                netloc=domain,
                                                path=''))):
            if path and funcs['is_reachable'](urlunparse(parsed_url._replace(
                                                            scheme=scheme,
                                                            netloc=domain,
                                                            path=path))):
                return urlunparse(parsed_url._replace(
                                        scheme=scheme,
                                        netloc=domain,
                                        path=path))
            return urlunparse(parsed_url._replace(
                                    scheme=scheme,
                                    netloc=domain,
                                    path=''))


# Получение URL в виде строки и возвращение схемы
def _correct_scheme(parsed_url: str, scheme: str) -> str:
    if parsed_url.scheme != scheme:  # Если URL не содержит схему
        '''
        Пример:
        url = 'https://www.google.com'
        parsed_url = ('HTML', 'www.google.com', '', '', '', '')
        parsed_url.scheme = ('www.google.com', '', '', '', '')
        '''
        # Возврат URL с валидной схемой
        return urlunparse(parsed_url._replace(scheme=scheme))
    return urlunparse(parsed_url)  # Возврат исходного URL


# Получение URL в виде строки и возвращение True или False
def _is_reachable(url: str) -> bool:
    # Список валидных кодов ответа
    valid_responses = [
        200,  # Успешный запрос
        301,  # Перенаправление
        302,  # Перенаправление
    ]
    timeout_ = 20
    try:
        # Получение ответа
        response = requests.get(url, timeout=timeout_, allow_redirects=True)
        # При успешном ответе возвращается True
        return response.status_code in valid_responses
    except requests.RequestException:  # Если возкает ошибка при запросе
        return False  # При ошибке возвращается False
    except requests.Timeout:
        return False  # При превышении времени ожидания возвращается 'Timeout'


# Получение URL в виде строки и возвращение домена
def _extract_domain(url: str) -> str:
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


def sanitize_url_input(user_input):
    cleaned_url = bleach.clean(user_input, strip=True)
    parsed_url = urlparse(cleaned_url)
    
    # Normalize the URL by keeping only scheme, netloc and removing trailing slashes
    normalized_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path.rstrip('/'),
        '',
        '',
        ''
    ))
    return normalized_url