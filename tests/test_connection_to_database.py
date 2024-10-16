import os
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from page_analyzer.app_repository import AppRepository
from datetime import datetime


@pytest.fixture(scope="module")
def db_conn():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    yield conn
    conn.close()

@pytest.fixture(scope="module")
def setup_db(db_conn):
    with db_conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS urls_table(
                id SERIAL PRIMARY KEY,
                url VARCHAR(255),
                creation_date DATE
            );
            CREATE TABLE IF NOT EXISTS checks_table(
                id SERIAL PRIMARY KEY,
                url_id INTEGER REFERENCES urls_table(id),
                check_id INTEGER,
                response_code INTEGER,
                h1_content TEXT,
                title_content TEXT,
                description_content TEXT,
                check_date DATE
            );
        ''')
        db_conn.commit()
    yield
    with db_conn.cursor() as cur:
        cur.execute('''
            DROP TABLE IF EXISTS checks_table;
            DROP TABLE IF EXISTS urls_table;
        ''')
        db_conn.commit()

@pytest.fixture
def repo(db_conn, setup_db):
    return AppRepository(db_conn)

def test_add_url(repo):
    url = "https://example.com"
    creation_date = datetime.now().strftime('%Y-%m-%d')
    url_id = repo.add_url(url, creation_date)
    assert url_id is not None

def test_get_urls(repo):
    urls = repo.get_urls()
    assert isinstance(urls, list)

def test_get_url_info(repo):
    url = "https://example.com"
    creation_date = datetime.now().strftime('%Y-%m-%d')
    url_id = repo.add_url(url, creation_date)
    url_info = repo.get_url_info(url_id['id'])
    assert url_info['url'] == url
    assert url_info['creation_date'] == creation_date

def test_get_url_checks(repo):
    url = "https://example.com"
    creation_date = datetime.now().strftime('%Y-%m-%d')
    url_id = repo.add_url(url, creation_date)
    checks = repo.get_url_checks(url_id['id'])
    assert isinstance(checks, list)

def test_get_url_address(repo):
    url = "https://example.com"
    creation_date = datetime.now().strftime('%Y-%m-%d')
    url_id = repo.add_url(url, creation_date)
    url_address = repo.get_url_address(url_id['id'])
    assert url_address['url'] == url

def test_check_url(repo):
    url = "https://example.com"
    creation_date = datetime.now().strftime('%Y-%m-%d')
    url_id = repo.add_url(url, creation_date)
    data = {
        'url': url,
        'response_code': 200,
        'h1_content': 'Example Domain',
        'title_content': 'Example Domain',
        'description_content': 'This domain is for use in illustrative examples in documents.',
        'check_date': creation_date
    }
    repo.check_url(data)
    checks = repo.get_url_checks(url_id['id'])
    assert len(checks) > 0
    assert checks[0]['response_code'] == 200