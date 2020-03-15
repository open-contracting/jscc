from unittest.mock import patch

import pytest
import requests

from jscc.testing.util import http_get, http_head, warn_and_assert


@patch('requests.head')
def test_http_head(meth):
    http_head('http://example.com')
    http_head('http://example.com')
    meth.assert_called_once()


@pytest.mark.vcr()
def test_http_head_error():
    with pytest.raises(requests.exceptions.HTTPError):
        http_head('http://httpbin.org/status/400')


@patch('requests.get')
def test_http_get(meth):
    http_get('http://example.com')
    http_get('http://example.com')
    meth.assert_called_once()


@pytest.mark.vcr()
def test_http_get_error():
    with pytest.raises(requests.exceptions.HTTPError):
        http_get('http://httpbin.org/status/400')


def test_warn_and_assert():
    with pytest.raises(AssertionError) as excinfo:
        with pytest.warns(UserWarning) as records:
            warn_and_assert([('path/',)], '{0} is invalid', 'See errors above')

    assert len(records) == 1
    assert str(records[0].message) == 'ERROR: path/ is invalid'
    assert str(excinfo.value) == 'See errors above'
