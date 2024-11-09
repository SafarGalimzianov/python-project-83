import os
import pytest
import psycopg
from datetime import datetime
from page_analyzer.app_repository import AppRepository


INCORRECT_INPUT_TYPES = [None, 1, 1.0, True, False, list(), dict(), set(), tuple()]
DATA = {'url': 'https://example.com', 'creation_date': '2000-01-01'}
DATA_DIFF_URL_SAME_DATE = {'url': 'https://not_example.com', 'creation_date': '2000-01-01'}
DATA_SAME_URL_DIFF_DATE = {'url': 'https://example.com', 'creation_date': '2000-01-02'}
DATA_DIFF_URL_DIFF_DATE = {'url': 'https://different.com', 'creation_date': '1970-01-01'}
CHECKS = [
    {
        'url': 'http://example.com',
        'response_code': 200,
        'h1': 'Welcome',
        'title': 'Example Domain',
        'description': 'This domain is for use in illustrative examples in documents.',
        'check_date': '2023-10-10'
    },
    {
        'url': 'http://example.com',
        'response_code': 301,
        'h1_content': 'Redirect',
        'title_content': 'Moved Permanently',
        'description': 'The resource has been moved permanently.',
        'check_date': '2023-10-11'
    },
]

column_types = {
    'url_id': int,
    'response_code': int,
    'h1': str,
    'title': str,
    'description': str,
    'check_date': str,  # Assuming dates are strings in the format 'YYYY-MM-DD'
}

BASE_CHECK_DATA = {
    'url_id': 1,
    'response_code': 200,
    'h1': 'Content',
    'title': 'Title',
    'description': 'Description',
    'check_date': '2023-10-05',
}

incorrect_type_dict = {}

for column, expected_type in column_types.items():
    invalid_entries = []
    for invalid in INCORRECT_INPUT_TYPES:
        if invalid is not None and not isinstance(invalid, expected_type):
            entry = BASE_CHECK_DATA.copy()
            entry[column] = invalid
            invalid_entries.append(entry)
    incorrect_type_dict[f"INCORRECT_{column}_TYPE"] = invalid_entries


INCORRECT_COLUMN_COUNT = []

# Пропуск отдельных столбцов
for column in BASE_CHECK_DATA.keys():
    entry = BASE_CHECK_DATA.copy()
    del entry[column]
    INCORRECT_COLUMN_COUNT.append(entry)

# Пропуск нескольких столбцов
columns = list(BASE_CHECK_DATA.keys())
for i in range(2, len(columns)):
    entry = BASE_CHECK_DATA.copy()
    for column in columns[:i]:
        del entry[column]
    INCORRECT_COLUMN_COUNT.append(entry)

# Добавление лишних столбцов
extra_fields = ['extra_field', 'extra1', 'extra2']
for extra in extra_fields:
    entry = BASE_CHECK_DATA.copy()
    entry[extra] = 'Extra'
    INCORRECT_COLUMN_COUNT.append(entry)

# Добавление нескольких лишних столбцов
entry = BASE_CHECK_DATA.copy()
entry['extra1'] = 'Extra1'
entry['extra2'] = 'Extra2'
INCORRECT_COLUMN_COUNT.append(entry)

# Пропуск всех столбцов
INCORRECT_COLUMN_COUNT.append({})

# Объединение всех некорректных данных
INCORRECT_CHECKS = []
for entries in incorrect_type_dict.values():
    INCORRECT_CHECKS.extend(entries)
INCORRECT_CHECKS.extend(INCORRECT_COLUMN_COUNT)

INCORRECT_URLS = {
    'long string': 'a' * 256,  # строка превышает максимальную длину в 255 символов
    'long URL': 'https://www.' + 'a' * 250 + '.com',  # Аналогично, но есть префикс и суффикс
}
INCORRECT_DATES = ['2-1-1', '02-01-01', '2000, 01, 01', '01-01-2000', '2000-01-01 00:00:00', '', 'YEAR-MONTH-DAY']

# Создание соединения с базой данных в рамках сессии
@pytest.fixture(scope="session")
def conn():
    with psycopg.connect(os.getenv('DATABASE_URL')) as conn: # Подключение к базе данных
        yield conn # Возвращение соединения не через return (иначе соединение будет закрыто)

# Создание транзакции в рамках соединения с базой данных
@pytest.fixture(autouse=True) # Автоматическое использование фикстуры применяется ко всем тестам
def transaction(conn):
    with conn.cursor() as cur: # Создание курсора
        cur.execute('BEGIN;') # Начало транзакции
    yield # Выполнение тестов
    with conn.cursor() as cur: # Создание курсора
        cur.execute('ROLLBACK;') # Откат транзакции

# Инстанцирование репозитория в рамках соединения с базой данных
@pytest.fixture
def repo(conn):
    return AppRepository(conn)

# Проверка метода добавленя URL
def test_add_url(repo: AppRepository):
    url, creation_date = DATA['url'], DATA['creation_date']
    url_id = repo.add_url(url, creation_date)
    assert url_id is not None
    # Добавление существующего URL
    url_id_same = repo.add_url(url, creation_date)
    assert url_id_same is not None
    assert url_id == url_id_same
    # Добавление нового URL с другим адресом и той же датой создания
    url_id_diff_url_same_date = repo.add_url(DATA_DIFF_URL_SAME_DATE['url'], DATA_DIFF_URL_SAME_DATE['creation_date'])
    assert url_id_diff_url_same_date is not None
    assert url_id != url_id_diff_url_same_date
    # Добавление существующего URL с другой датой создания
    url_id_same_url_diff_date = repo.add_url(DATA_SAME_URL_DIFF_DATE['url'], DATA_SAME_URL_DIFF_DATE['creation_date'])
    assert url_id_same_url_diff_date is not None
    assert url_id_same_url_diff_date == url_id
    assert url_id_same_url_diff_date != url_id_diff_url_same_date


def test_add_url_errors(repo: AppRepository):
    # Тест с неверными типами входных данных
    for invalid_input in INCORRECT_INPUT_TYPES:
        with pytest.raises((psycopg.errors.NotNullViolation, TypeError)):
            repo.add_url(invalid_input, DATA['creation_date'])
        with pytest.raises((psycopg.errors.NotNullViolation, TypeError)):
            repo.add_url(DATA['url'], invalid_input)

    # Тест с некорректными URL
    long_string = INCORRECT_URLS['long string']
    long_url = INCORRECT_URLS['long URL']
    with pytest.raises(psycopg.errors.StringDataRightTruncation):
        repo.add_url(long_string, DATA['creation_date'])

    with pytest.raises(psycopg.errors.InFailedSqlTransaction):
        repo.add_url(long_url, DATA['creation_date'])

    # Тест с некорректными датами
    for invalid_date in INCORRECT_DATES:
        # psycopg.errors.InvalidDatetimeFormat
        with pytest.raises(psycopg.errors.InFailedSqlTransaction):
            repo.add_url(DATA['url'], invalid_date)

    # Тест с корректными URL и датой
    url, creation_date = DATA['url'], DATA['creation_date']
    # Закрытие соединения с базой данных
    repo.conn.close()
    # Попытка добавить данные при закрытом соединении
    with pytest.raises(psycopg.errors.OperationalError):
        repo.add_url(url, creation_date)

def test_check_url(repo: AppRepository):
    # Корректные URL и дата создания
    url, creation_date = DATA['url'], DATA['creation_date']
    
    # Добавление URL
    url_id = repo.add_url(url, creation_date)
    assert url_id is not None
    
    # Подготовка данных проверки
    check_data = {
        'url': url,
        'response_code': CHECKS[0]['response_code'],
        'h1': CHECKS[0]['h1'],
        'title': CHECKS[0]['title'],
        'description': CHECKS[0]['description'],
        'check_date': CHECKS[0]['check_date']
    }
    
    # Вызов проверки URL
    repo.check_url(check_data)
    
    # Получение проверок URL
    checks = repo.get_url_checks(url_id['id'])
    inserted_check = checks[len(checks) - 1]
    
    # Проверка добавленных данных
    assert inserted_check['response_code'] == check_data['response_code']
    assert inserted_check['h1_content'] == check_data['h1']
    assert inserted_check['title_content'] == check_data['title']
    assert inserted_check['description_content'] == check_data['description']
    assert inserted_check['check_date'].strftime('%Y-%m-%d') == check_data['check_date']
    
    # Тест с неверным URL
    invalid_check_data = {
        'url': 'non_existent_url',
        'response_code': 200,
        'h1_content': 'Content',
        'title_content': 'Title',
        'description_content': 'Description',
        'check_date': '2023-10-05'
    }
    
    with pytest.raises(ValueError) as exc_info:
        repo.check_url(invalid_check_data)
    assert str(exc_info.value) == 'URL not found in urls_list'

def test_check_url_errors(repo: AppRepository):
    # Тест с некорректными данными
    for invalid_data in INCORRECT_CHECKS:
        with pytest.raises((psycopg.errors.NotNullViolation, psycopg.errors.StringDataRightTruncation, TypeError, KeyError)):
            repo.check_url(invalid_data)

    # Тест с некорректным числом столбцов
    for invalid_data in INCORRECT_COLUMN_COUNT:
        with pytest.raises((psycopg.errors.NotNullViolation, psycopg.errors.StringDataRightTruncation, psycopg.errors.ForeignKeyViolation, KeyError)):
            repo.check_url(invalid_data)

    # Тест с некорректным URL
    for invalid_url in INCORRECT_URLS:
        check_data = BASE_CHECK_DATA.copy()
        check_data['url'] = invalid_url
        with pytest.raises(psycopg.errors.StringDataRightTruncation):
            repo.check_url(check_data)

    # Тест с некорреткной датой
    for invalid_date in INCORRECT_DATES:
        check_data = BASE_CHECK_DATA.copy()
        check_data['check_date'] = invalid_date
        with pytest.raises(psycopg.errors.InvalidDatetimeFormat):
            repo.check_url(check_data)

    # Test with non-existent URL
    invalid_check_data = BASE_CHECK_DATA.copy()
    invalid_check_data['url'] = 'non_existent_url'
    with pytest.raises(ValueError) as exc_info:
        repo.check_url(invalid_check_data)
    assert str(exc_info.value) == 'URL not found in urls_list'

    # Test with closed database connection
    repo.conn.close()
    with pytest.raises(psycopg.errors.InterfaceError):
        repo.check_url(BASE_CHECK_DATA)