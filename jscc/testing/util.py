"""Miscellaneous methods, mainly used by other repositories."""

import warnings
from functools import lru_cache

import requests


@lru_cache
def http_get(url):
    """
    Send and cache an HTTP GET request.

    .. attention:: No timeout is set. If a user can input a malicious URL, the program can hang indefinitely.

    :param str url: the URL to request
    """
    response = requests.get(url)  # noqa: S113
    response.raise_for_status()
    return response


@lru_cache
def http_head(url):
    """
    Send and cache an HTTP HEAD request.

    .. attention:: No timeout is set. If a user can input a malicious URL, the program can hang indefinitely.

    :param str url: the URL to request
    """
    response = requests.head(url)  # noqa: S113
    response.raise_for_status()
    return response


def difference(actual, expected):
    """
    Return strings describing the differences between actual and expected sets.

    Example::

        >>> difference({1, 2, 3}, {3, 4, 5})
        ('; added {1, 2}', '; removed {4, 5}')

        >>> difference({1}, {1})
        ('', '')

    :param set actual: the actual set
    :param set expected: the expected set
    """
    added = actual - expected
    added = f"; added {added}" if added else ""

    removed = expected - actual
    removed = f"; removed {removed}" if removed else ""

    return added, removed


def warn_and_assert(paths, warn_message, assert_message):
    """
    If ``paths`` isn't empty, issue a warning for each path, and raise an assertion error.

    :param list paths: file paths
    :param str warn_message: the format string for the warning message
    :param str assert_message: the error message for the assert statement
    """
    success = True
    for args in paths:
        warnings.warn("ERROR: " + warn_message.format(*args))
        success = False

    assert success, assert_message  # noqa: S101 # false positive
