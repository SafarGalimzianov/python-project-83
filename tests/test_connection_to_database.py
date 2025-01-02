import os
import psycopg2
import psycopg2.errors
import pytest
import random
import string
from datetime import datetime
from page_analyzer.app_repository import AppRepository

from dotenv import load_dotenv

load_dotenv()


def generate_random_url():
    domain = ''.join(random.choices(string.ascii_lowercase, k=10))
    tld = random.choice(['com', 'org', 'net', 'io'])
    return f"https://{domain}.{tld}"


@pytest.fixture(scope='session')
def setup_session():
    if not os.getenv('DATABASE_URL'):
        pytest.skip("DATABASE_URL environment variable not set")
    return True


@pytest.fixture(autouse=True)
def transaction_rollback(setup_session):
    database_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    conn.autocommit = False

    with conn.cursor() as cur:
        cur.execute('BEGIN;')

    yield conn

    conn.rollback()
    conn.close()


@pytest.fixture
def repository(transaction_rollback):
    return AppRepository(transaction_rollback)


def test_add_and_get_url(repository):
    url = generate_random_url()
    date = datetime.now().strftime('%Y-%m-%d')

    url_info = repository.get_urls()
    assert not any(info['url'] == url for info in url_info)

    url_id = repository.add_url(url, date)
    assert url_id is not None

    url_info = repository.get_url_info(url_id['id'])
    assert url_info['url'] == url
    assert url_info['creation_date'].strftime('%Y-%m-%d') == date

    modified_url = url.replace('https://', 'http://')
    assert not \
        any(info['url'] == modified_url for info in repository.get_urls())


def test_url_checks(repository):
    url = generate_random_url()
    date = datetime.now().strftime('%Y-%m-%d')

    url_info = repository.get_urls()
    assert not any(info['url'] == url for info in url_info)

    url_id = repository.add_url(url, date)

    check_data = {
        'url': url,
        'response_code': 200,
        'h1': 'Test H1',
        'title': 'Test Title',
        'description': 'Test Description',
        'check_date': date
    }

    repository.check_url(check_data)

    checks = repository.get_url_checks(url_id['id'])
    assert len(checks) == 1
    assert checks[0]['response_code'] == 200
    assert checks[0]['h1_content'] == 'Test H1'


def test_edge_case_urls(repository):
    with pytest.raises(TypeError):
        repository.add_url(None, datetime.now().strftime('%Y-%m-%d'))

    special_url = "https://example.com/!@#$%^&*()"
    date = datetime.now().strftime('%Y-%m-%d')
    url_id = repository.add_url(special_url, date)
    assert url_id is not None
    url_info = repository.get_url_info(url_id['id'])
    assert url_info['url'] == special_url

    url_id = None
    long_domain = 'a' * 245
    long_url = f"https://{long_domain}.com"
    with pytest.raises(psycopg2.errors.StringDataRightTruncation):
        url_id = repository.add_url(long_url, date)
    assert url_id is None

    unicode_url = "https://测试.com"
    with pytest.raises(psycopg2.errors.InFailedSqlTransaction):
        url_id = repository.add_url(unicode_url, date)
    assert url_id is None

    invalid_url = "https://exa mple.com/path with spaces"
    with pytest.raises(psycopg2.errors.InFailedSqlTransaction):
        repository.add_url(invalid_url, date)
    assert url_id is None


def test_edge_case_dates(repository):
    url = generate_random_url()

    with pytest.raises(psycopg2.errors.InvalidDatetimeFormat):
        repository.add_url(url, "invalid-date")

    future_date = "2099-12-31"
    with pytest.raises(psycopg2.errors.InFailedSqlTransaction):
        repository.add_url(url, future_date)