from page_analyzer.app import make_request


TEST_URLS = {
    200: 'https://www.example.com',
    404: 'https://httpstat.us/404',
    500: 'https://httpstat.us/500',
    429: 'https://httpstat.us/429',
    0: 'http://this-site-definitely-does-not-exist.com',
    1: 'http://localhost:1'
}

RESPONSES_WITH_FIX = {
    code: make_request(url) for code, url in TEST_URLS.items()
    }
RESPONSES_WITHOUT_FIX = {
    code: make_request(url, fix=False) for code, url in TEST_URLS.items()
    }


def test_make_request_valid_url():
    result = RESPONSES_WITH_FIX[200]
    result_ = RESPONSES_WITHOUT_FIX[200]

    assert result == result_
    assert result['name'] == TEST_URLS[200]
    assert result['status_code'] == 200
    assert isinstance(result['h1'], str)
    assert isinstance(result['title'], str)
    assert isinstance(result['description'], str)
    assert isinstance(result['created_at'], str)


'''
def test_make_request_not_found():
    result = RESPONSES_WITH_FIX[404]
    assert result['status_code'] == 200

    result = RESPONSES_WITHOUT_FIX[404]
    assert result['status_code'] == 404


def test_make_request_server_error():
    result = RESPONSES_WITH_FIX[500]
    assert result['status_code'] == 200

    result = RESPONSES_WITHOUT_FIX[500]
    assert result['status_code'] == 500


def test_make_request_rate_limit():
    result = RESPONSES_WITH_FIX[429]
    assert result['status_code'] == 200

    result = RESPONSES_WITHOUT_FIX[429]
    assert result['status_code'] == 429
'''


def test_make_request_dns_error():
    result = RESPONSES_WITH_FIX[0]
    assert result['name'] is False


def test_make_request_connection_error():
    result = RESPONSES_WITH_FIX[1]
    assert result['name'] is False
