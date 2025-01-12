from os import getenv
import pytest
import json
import requests
import random
from page_analyzer.service import make_request, REQUEST_TIMEOUT

APP_URL = getenv('APP_URL')
LOG_FILE = 'app.log'
ADD_URL_STATUS_CODES = (
    302,
    422
)
CHECK_URL_STATUS_CODES = (
    302,
    404
)


session = requests.Session()


def get_random_urls(urls: list):
    num_of_urls = 2
    result = []
    for _ in range(num_of_urls):
        result.append('https://'+random.choice(urls))

    return result


@pytest.fixture(scope='module')
def load_urls():
    with open('tests/fixtures/urls.json', 'r') as f:
        data = json.load(f)
        return get_random_urls(list(data.values()))


@pytest.fixture(scope='session', autouse=True)
def clear_logs():
    yield

    with open(LOG_FILE, 'w') as log_file:
        log_file.truncate()
    print('Логи удалены после теста')


def test_make_request(load_urls):
    responses = []
    make_request_responses = []
    for url in load_urls:
        responses.append(session.get(url, timeout=REQUEST_TIMEOUT).status_code)
        make_request_responses.append(make_request(url)['status_code'])

    assert any(response == make_request_response
               for response, make_request_response
               in zip(responses, make_request_responses)), (
                    'Должно быть хотя бы одно совпадение кодов ответов'
                )


def test_add_url(load_urls):
    for url in load_urls:
        add_response = requests.post(
            f'{APP_URL}/urls',
            data={'url': url}
        )
        assert add_response.status_code in ADD_URL_STATUS_CODES, (
            f'Unexpected response code: {add_response}'
        )


def test_check_url(load_urls):
    for url in load_urls:
        add_response = requests.post(
            f'{APP_URL}/urls',
            data={'url': url}
        )
        assert add_response.status_code in ADD_URL_STATUS_CODES, (
            f'Unexpected response code: {add_response}'
        )
        if add_response.status_code == 302:
            location = add_response.headers['Location']
            url_id = int(location.split('/')[-1])

            check_response = requests.post(
                f'{APP_URL}/urls/{url_id}'
            )

            assert check_response.status_code in CHECK_URL_STATUS_CODES, (
                f'Unexpected response code: {check_response}'
            )
