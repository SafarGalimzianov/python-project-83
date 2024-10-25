import os
import pytest
import psycopg
from psycopg.rows import DictRow
from page_analyzer.app_repository import AppRepository


# Создание соединения с базой данных в рамках сессии
@pytest.fixture(scope="session")
def connection():
    with psycopg.connect(os.getenv('DATABASE_URL')) as conn: # Подключение к базе данных
        yield conn # Возвращение соединения не через return (иначе соединение будет закрыто)

# Создание транзакции в рамках соединения с базой данных
@pytest.fixture(autouse=True) # Автоматическое использование фикстуры применяется ко всем тестам
def transatction(conn):
    with conn.cursor() as cur: # Создание курсора
        cur.execute('BEGIN;') # Начало транзакции
    # Курсор закрывается автоматически 
    yield # Выполнение тестов
    with conn.cursor() as cur:
        cur.execute('ROLLBACK;')

@pytest.fixture
def repo(conn):
    return AppRepository(conn)

def test_add_url(repo):
    url = 'https://example.com'