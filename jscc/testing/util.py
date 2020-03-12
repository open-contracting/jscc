import warnings


def true():
    return True


def false():
    return False


def tracked(path):
    """
    Returns whether the path isn't typically untracked in Git repositories.
    """
    substrings = {
        '.egg-info/',
        '/.tox/',
        '/.ve/',
        '/htmlcov/',
        '/node_modules/',
    }

    return not any(substring in path for substring in substrings)


def warn_and_assert(paths, warn_message, assert_message):
    """
    If ``paths`` isn't empty, issues a warning for each path, and raises an assertion error.
    """
    success = True
    for path in paths:
        warnings.warn('ERROR: ' + warn_message.format(path=path))
        success = False

    assert success, assert_message


def is_json_schema(data):
    """
    Returns whether the data is a JSON Schema.
    """
    return '$schema' in data or 'definitions' in data or 'properties' in data


def is_codelist(reader):
    """
    Returns whether the CSV is a codelist.
    """
    return 'Code' in reader.fieldnames


def is_array_of_objects(data):
    """
    Returns whether the field is an array of objects.
    """
    return 'array' in data.get('type', []) and any(key in data.get('items', {}) for key in ('$ref', 'properties'))


def get_types(data):
    """
    Returns a field's `type` as a list.
    """
    if 'type' not in data:
        return []
    if isinstance(data['type'], str):
        return [data['type']]
    return data['type']


def collect_codelist_values(path, data, pointer=''):
    """
    Collects `codelist` values from JSON Schema.
    """
    codelists = set()

    if isinstance(data, list):
        for index, item in enumerate(data):
            codelists.update(collect_codelist_values(path, item, pointer='{}/{}'.format(pointer, index)))
    elif isinstance(data, dict):
        if 'codelist' in data:
            codelists.add(data['codelist'])

        for key, value in data.items():
            codelists.update(collect_codelist_values(path, value, pointer='{}/{}'.format(pointer, key)))

    return codelists


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


def traverse(block):
    """
    Implements common logic used by methods below.
    """
    def method(path, data, pointer=''):
        errors = 0

        if isinstance(data, list):
            for index, item in enumerate(data):
                errors += method(path, item, pointer='{}/{}'.format(pointer, index))
        elif isinstance(data, dict):
            errors += block(path, data, pointer)

            for key, value in data.items():
                errors += method(path, value, pointer='{}/{}'.format(pointer, key))

        return errors

    return method
