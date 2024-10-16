import os
import pytest
import pook
from flask import Flask
from page_analyzer.app import app, make_request, validate_and_fix_url, get_current_date, format_date


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv('SECRET_KEY', 'test_secret_key')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://test_user:test_password@localhost/test_db')

@pook.on
def test_make_request_success():
    url = 'https://www.example.com'
    pook.get(url, reply=200, response_json={
        'h1': 'Example Domain',
        'title': 'Example Domain',
        'meta': {'description': 'This domain is for use in illustrative examples in documents.'}
    })

    response = make_request(url)
    assert response['url'] == url
    assert response['response_code'] == 200
    assert response['h1_content'] == 'Example Domain'
    assert response['title_content'] == 'Example Domain'
    assert response['description_content'] == 'This domain is for use in illustrative examples in documents.'

@pook.on
def test_make_request_failure():
    url = 'https://www.nonexistenturl.com'
    pook.get(url, reply=404)

    response = make_request(url)
    assert response['url'] == False

def test_get_current_date():
    assert get_current_date() == datetime.now().strftime('%Y-%m-%d')

def test_format_date():
    assert format_date('Wed, 21 Oct 2015 07:28:00 GMT') == '2015-10-21'
    assert format_date('Invalid Date') == get_current_date()

def test_search_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Search' in response.data

def test_add_url_route(client):
    response = client.post('/', data={'url': 'https://www.example.com'})
    assert response.status_code == 302  # Redirect

def test_get_url_route(client):
    response = client.get('/url/1')
    assert response.status_code == 404  # Assuming no URL with id 1 exists

def test_check_url_route(client):
    response = client.post('/url/1')
    assert response.status_code == 404  # Assuming no URL with id 1 exists

def test_get_urls_route(client):
    response = client.get('/urls')
    assert response.status_code == 200
    assert b'URLs' in response.data

def test_get_content_route(client):
    response = client.get('/content')
    assert response.status_code == 200
    assert b'data' in response.data

def test_404_error_handler(client):
    response = client.get('/nonexistentpage')
    assert response.status_code == 404
    assert b'404' in response.data