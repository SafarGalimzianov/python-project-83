import pytest
import pook
from page_analyzer.app import app, make_request, validate_and_fix_url, get_current_date, format_date

TEST_URL = 'https://nonexistent.example.com/'

# Создание тестового клиента
@pytest.fixture
def client():
    app.config['TESTING'] = True # Смена среды с рабочей на тестовую
    with app.test_client() as client: # Создание тестового клиента
        yield client
    app.config['TESTING'] = False # Смена среды с тестовой на рабочую

# Успешный тест функции запроса URL
def test_make_request_success():
    with pook.use():
        pook.get(TEST_URL).reply(200).body(
            '<html><head><title>Example</title>'
            '<meta name="description" content="Test description"/>'
            '</head><body><h1>Example Header</h1></body></html>'
        ).headers({'Date': 'Wed, 21 Oct 2015 07:28:00 GMT'})

        result = make_request(TEST_URL)
        assert result['url'] == TEST_URL.rstrip('/')
        assert result['response_code'] == 200
        assert result['h1_content'] == 'Example Header'
        assert result['title_content'] == 'Example'
        assert result['description_content'] == 'Test description'
        assert result['check_date'] == '2015-10-21'

# Тест функции запроса URL с ошибкой
def test_make_request_failure():
    with pook.use():
        pook.get(TEST_URL.replace('nonexistent', 'invalid-example')).reply(404)
        result = make_request(TEST_URL.replace('nonexistent', 'invalid-example'))
        assert result['url'] is False

# Тес�� функции проверки и исправления URl
def test_validate_and_fix_url():
    """Test URL validation and fixing"""
    # Верные URL
    assert validate_and_fix_url(TEST_URL) == TEST_URL
    assert validate_and_fix_url(TEST_URL.replace('https', 'http')) == TEST_URL.replace('https', 'http')
    
    # Некорретные URL, которые д��лжны были быть исправлены
    assert validate_and_fix_url('example.com') in [TEST_URL, TEST_URL.replace('https', 'http')]
    assert validate_and_fix_url('www.example.com') in [TEST_URL.replace('nonexistent', 'www'), TEST_URL.replace('https', 'http').replace('nonexistent', 'www')]
    
    # Некорретные и неисправляемые URL
    assert not validate_and_fix_url('invalid://example.com')
    assert not validate_and_fix_url('not-a-url')

# Проверка маршрутов с тестовым клиентом
def test_routes(client):
    # Главная страница всегда доступна
    response = client.get('/')
    assert response.status_code == 200
    
    # Страница со списком URL всегда доступна
    response = client.get('/urls')
    assert response.status_code == 200
    
    # После добавления URL должно быть перенаправление
    response = client.post('/', data={'url': TEST_URL})
    assert response.status_code == 302  # Redirect
    
    # Страница URL по его id должна быть или успешна, или возвращать 404 при отсутсвии такого id
    response = client.get('/url/1')
    assert response.status_code in [200, 404]
    
    # Страница проверки URl по его id должна быть успешна и тогда происходит перенаправление на страницу URl
    # или возвращать 404 при отсутсвии такого id
    response = client.post('/url/1')
    assert response.status_code in [302, 404]  # Redirect or Not Found

# Проверка обработчиков ошибок
def test_error_handlers(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404

    response = client.get('/url/one')
    assert response.status_code == 404

    response = client.get('/non')
    assert response.status_code == 404
