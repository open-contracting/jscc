"""
Miscellaneous methods, mainly used by other repositories.
"""

import warnings
from functools import lru_cache

import requests


@lru_cache()
def http_get(url):
    """
    Sends and caches an HTTP GET request.

    :param str url: the URL to request
    """
    response = requests.get(url)
    response.raise_for_status()
    return response


@lru_cache()
def http_head(url):
    """
    Sends and caches an HTTP HEAD request.

    :param str url: the URL to request
    """
    response = requests.head(url)
    response.raise_for_status()
    return response


def difference(actual, expected):
    """
    Returns strings describing the differences between actual and expected sets.

    Example::

        >>> difference({1, 2, 3}, {3, 4, 5})
        ('; added {1, 2}', '; removed {4, 5}')

        >>> difference({1}, {1})
        ('', '')

    :param set actual: the actual set
    :param set expected: the expected set
    """
    added = actual - expected
    if added:
        added = f'; added {added}'
    else:
        added = ''

    removed = expected - actual
    if removed:
        removed = f'; removed {removed}'
    else:
        removed = ''

    return added, removed


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
