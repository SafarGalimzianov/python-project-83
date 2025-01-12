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
