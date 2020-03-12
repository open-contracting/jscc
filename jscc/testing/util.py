import warnings
from collections import UserDict

from jscc.exceptions import DuplicateKeyError


def tracked(path):
    """
    Returns whether the path isn't typically untracked in Git repositories.

    :param str path: a file path
    """
    substrings = {
        '.egg-info/',
        '/.tox/',
        '/.ve/',
        '/htmlcov/',
        '/node_modules/',
    }

    return not any(substring in path for substring in substrings)


def is_codelist(reader):
    """
    Returns whether the CSV is a codelist.

    :param csv.DictReader reader: A CSV reader
    """
    return 'Code' in reader.fieldnames


class RejectingDict(UserDict):
    """
    Raises an error if a key is set more than once.
    """
    # See https://tools.ietf.org/html/rfc7493#section-2.3
    def __setitem__(self, k, v):
        if k in self:
            raise DuplicateKeyError(k)
        return super().__setitem__(k, v)


def rejecting_dict(pairs):
    """
    An ``object_pairs_hook`` method that allows a key to be set at most once.
    """
    # Return the wrapped dict, not the RejectingDict itself, because jsonschema checks the type.
    return RejectingDict(pairs).data


def difference(actual, expected):
    """
    Returns strings describing the differences between actual and expected values.
    """
    added = actual - expected
    if added:
        added = '; added {}'.format(added)
    else:
        added = ''

    removed = expected - actual
    if removed:
        removed = '; removed {}'.format(removed)
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


def true():
    """
    Returns ``True``.
    """
    return True


def false():
    """
    Returns ``False``.
    """
    return False
