import os
import pytest
from datetime import datetime
import pook
from flask import Flask
from page_analyzer.app import app, make_request, validate_and_fix_url, get_current_date, format_date

TEST_URL = 'https://nonexistent.example.com/'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

'''
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv('SECRET_KEY', 'test_secret_key')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://test_user:test_password@localhost/test_db')
'''
def test_make_request_success():
    url = TEST_URL
    
    mock_html = '''
    <html>
        <head>
            <title>Example Test Page</title>
            <meta name="description" content="Example Test Description">
        </head>
        <body>
            <h1>Example Test Header</h1>
        </body>
    </html>
    '''

    with pook.use():
        pook.get(url).reply(200).headers({
            'Date': 'Wed, 21 Oct 2023 07:28:00 GMT'
        }).body(mock_html)
        
        response = make_request(url)
        assert response['url'] == url
        assert response['response_code'] == 200
        assert response['h1'] == 'Example Test Header'
        assert response['title'] == 'Example Test Page'
        assert response['description'] == 'Example Test Description'
        assert response['check_date'] == '2023-10-21'

def test_make_request_failure():

    url = TEST_URL
    
    mock_html = '''
    <html>
        <head>
            <title>Example Test Page</title>
            <meta name="description" content="Example Test Description">
        </head>
        <body>
            <h1>Example Test Header</h1>
        </body>
    </html>
    '''
    
    with pook.use():
        pook.get(url).reply(500).headers({
            'Date': 'Wed, 21 Oct 2023 07:28:00 GMT'
        }).body(mock_html)
        
        response = make_request(url)
        assert response['url'] == False

def test_make_request_redirect():
    url = TEST_URL

    with pook.use():
        # Test 2: HTTP to HTTPS redirect
        pook.get(url).reply(301).headers({
            'Location': url
        })
        pook.get(url).reply(200).headers({
            'Date': 'Wed, 21 Oct 2023 07:28:00 GMT'
        }).body('<html><body>Redirected</body></html>')
        
        response = make_request(url)
        assert response['url'] == url
        assert response['response_code'] == 200

def test_make_request_invalid_url():
    url = TEST_URL

    # Test 3: Invalid URL
    response = make_request('not-a-url')
    assert response['url'] is False

def test_make_request_missing_elements():
    url = TEST_URL

    with pook.use():
        # Test 4: Missing HTML elements
        pook.get(url).reply(200).body('<html><body></body></html>')
        
        response = make_request(url)
        assert response['h1'] == ''
        assert response['title'] == ''
        assert response['description'] == ''

def test_make_request_missing_date():
    url = TEST_URL

    with pook.use():
        # Test 5: Missing date header
        pook.get(url).reply(200).body('<html><body>Test</body></html>')
        
        response = make_request(url)
        assert response['check_date'] == datetime.now().strftime('%Y-%m-%d')

def test_get_current_date():
    assert get_current_date() == datetime.now().strftime('%Y-%m-%d')

def test_format_date():
    assert format_date('Wed, 21 Oct 2015 07:28:00 GMT') == '2015-10-21'
    assert format_date('Invalid Date') == get_current_date()

def test_search_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_add_url_route(client):
    url = TEST_URL

    response = client.post('/', data={'url': url})
    assert response.status_code == 302  # Redirect

def test_get_url_route(client):
    response = client.get('/url/1')
    assert response.status_code in (200, 404)

def test_check_url_route(client):
    response = client.post('/url/1')
    assert response.status_code in (302, 404)  # Assuming no URL with id 1 exists

def test_get_urls_route(client):
    response = client.get('/urls')
    assert response.status_code == 200

def test_404_error_handler(client):
    response = client.get('/nonexistentpage')
    assert response.status_code == 404