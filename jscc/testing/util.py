import warnings


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

    :param csv.reader reader: A CSV reader
    """
    return 'Code' in reader.fieldnames


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
    for path in paths:
        warnings.warn('ERROR: ' + warn_message.format(path=path))
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
