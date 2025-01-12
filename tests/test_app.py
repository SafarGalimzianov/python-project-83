import pytest
from unittest.mock import patch
from page_analyzer.app import app
from page_analyzer.service import make_request


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_urls():
    return ['https://example.com', 'https://test.com']


@pytest.fixture
def mock_html():
    return '''
        <html>
            <head>
                <title>Test Title</title>
                <meta name="description" content="Test Description">
            </head>
            <body>
                <h1>Test H1</h1>
            </body>
        </html>
    '''


def test_make_request(mock_urls, mock_html):
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = mock_html

        response = make_request(mock_urls[0])

        assert response['status_code'] == 200
        assert response['h1'] == 'Test H1'
        assert response['title'] == 'Test Title'
        assert response['description'] == 'Test Description'


def test_add_url(client, mock_urls):
    with patch('page_analyzer.app_repository.AppRepository.add_url')\
            as mock_add:
        mock_add.return_value = {'id': 1}

        response = client.post('/urls', data={'url': mock_urls[0]})
        assert response.status_code == 302

        response = client.post('/urls', data={'url': 'invalid-url'})
        assert response.status_code == 422


def test_check_url(client, mock_urls):
    with patch(
        'page_analyzer.app_repository.AppRepository.get_url_name_by_id'
            )as mock_get_name:
        mock_get_name.return_value = {'name': mock_urls[0]}

        # get_url_id_by_name будет пытаться найти url в базе данных
        # поэтому его тоже изолируем при помощи Mock
        with patch(
            'page_analyzer.app_repository.AppRepository.get_url_id_by_name'
                ) as mock_get_id:
            mock_get_id.return_value = {'id': 1}

            with patch('page_analyzer.service.make_request') as mock_request:
                mock_request.return_value = {
                    'name': mock_urls[0],
                    'status_code': 200,
                    'h1': 'Test H1',
                    'title': 'Test Title',
                    'description': 'Test Description'
                }

                response = client.post('/urls/1')
                assert response.status_code == 302
