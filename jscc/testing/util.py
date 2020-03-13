import warnings
from collections import UserDict
from functools import lru_cache

import requests

from jscc.exceptions import DuplicateKeyError


@lru_cache()
def http_get(url):
    """
    Sends and caches an HTTP GET request.

    :param str url: the URL to request
    """
    return requests.get(url)


@lru_cache()
def http_head(url):
    """
    Sends and caches an HTTP HEAD request.

    :param str url: the URL to request
    """
    return requests.head(url)


def warn_and_assert(paths, warn_message, assert_message):
    """
    If ``paths`` isn't empty, issues a warning for each path, and raises an assertion error.

    :param list paths: file paths
    :param str warn_message: the format string for the warning message
    :param str assert_message: the error message for the assert statement
    """
    success = True
    for args in paths:
        warnings.warn('ERROR: ' + warn_message.format(*args))
        success = False

    assert success, assert_message
