from os import getenv
import pytest
from datetime import date
from page_analyzer.db_pool import ConnectionPool
from page_analyzer.app_repository import AppRepository


@pytest.fixture(scope='session')
def test_db_url():
    return getenv('DATABASE_URL')


@pytest.fixture(scope='session')
def connection_pool(test_db_url):
    pool = ConnectionPool(db_url=test_db_url)
    pool.init_pool()
    return pool


@pytest.fixture(scope='function')
def db_connection(connection_pool):
    with connection_pool.get_cursor() as cur:
        yield connection_pool
        cur.execute("ROLLBACK;")


def test_add_url(db_connection):
    repo = AppRepository(pool=db_connection)
    creation_date = date.today().isoformat()
    url_name = "https://test-example.com"

    result = repo.add_url(url_name, creation_date)
    assert result['id'] is not None

    with db_connection.get_cursor() as cur:
        cur.execute("SELECT * FROM urls WHERE url = %s", (url_name,))
        url = cur.fetchone()
        assert url is not None
        assert url['url'] == url_name


def test_get_url_id_by_name(db_connection):
    repo = AppRepository(pool=db_connection)
    creation_date = date.today().isoformat()
    url_name = "https://test-example.com"

    repo.add_url(url_name, creation_date)

    result = repo.get_url_id_by_name(url_name)
    assert result['id'] is not None

def test_get_urls_paginated(db_connection):
    repo = AppRepository(pool=db_connection)
    creation_date = date.today().isoformat()
    url_name = "https://test-example.com"

    repo.add_url(url_name, creation_date)

    urls, total = repo.get_urls_paginated(page=1, per_page=10)
    assert len(urls) > 0
    assert total > 0
    assert isinstance(urls[0], dict)
    assert 'id' in urls[0]
    assert 'name' in urls[0]

def test_get_url_info(db_connection):
    repo = AppRepository(pool=db_connection)
    creation_date = date.today().isoformat()
    url_name = "https://test-example.com"

    url_id = repo.add_url(url_name, creation_date)['id']

    url_info = repo.get_url_info(url_id)
    assert url_info is not None
    assert url_info['name'] == url_name
    assert url_info['created_at'].isoformat() == creation_date

def test_get_url_checks(db_connection):
    repo = AppRepository(pool=db_connection)
    creation_date = date.today().isoformat()
    url_name = "https://test-example.com"

    url_id = repo.add_url(url_name, creation_date)['id']

    check_data = {
        'name': url_name,
        'status_code': 200,
        'h1': 'Test H1',
        'title': 'Test Title',
        'description': 'Test Description'
    }
    repo.check_url(check_data, creation_date)

    checks = repo.get_url_checks(url_id)
    assert len(checks) > 0
    assert checks[0]['check_id'] == 1
    assert checks[0]['status_code'] == 200

def test_get_url_name_by_id(db_connection):
    repo = AppRepository(pool=db_connection)
    creation_date = date.today().isoformat()
    url_name = "https://test-example.com"

    url_id = repo.add_url(url_name, creation_date)['id']

    url_data = repo.get_url_name_by_id(url_id)
    assert url_data is not None
    assert url_data['name'] == url_name