import os
import pytest
import psycopg
from psycopg.rows import DictRow
from page_analyzer.app_repository import AppRepository



@pytest.fixture(scope="session")
def connection():
    with psycopg.connect(os.getenv('DATABASE_URL')) as conn:
        yield conn

@pytest.fixture(autouse=True)
def transatction(conn):
    with conn.cursor() as cur:
        cur.execute('BEGIN;')
    yield
    with conn.cursor() as cur:
        cur.execute('ROLLBACK;')

@pytest.fixture
def repo(conn):
    return AppRepository(conn)

def test_add_url(repo):
    url = 'https://example.com'