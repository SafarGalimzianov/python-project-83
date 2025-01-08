from page_analyzer.service import make_request


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
    assert 'error' not in result
    assert result['status_code'] == 200
    assert isinstance(result['h1'], str)
    assert isinstance(result['title'], str)


def test_make_request_not_found():
    '''
    result = RESPONSES_WITH_FIX[404]
    assert 'error' not in result
    assert result['status_code'] == 200
    
    result = RESPONSES_WITHOUT_FIX[404]
    assert 'error' not in result
    assert result['status_code'] == 404
    '''


def test_make_request_server_error():
    '''
    result = RESPONSES_WITH_FIX[500]
    assert 'error' not in result
    assert result['status_code'] == 200
    
    result = RESPONSES_WITHOUT_FIX[500]
    assert 'error' not in result
    assert result['status_code'] == 500
    '''


def test_make_request_dns_error():
    result = RESPONSES_WITH_FIX[0]
    assert result['name'] is False
    assert 'error' in result


def test_make_request_connection_error(): 
    result = RESPONSES_WITH_FIX[1]
    assert result['name'] is False
    assert 'error' in result