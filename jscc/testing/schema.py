"""
Methods for reading JSON Schema and CSV codelists.
"""

def is_codelist(reader):
    """
    Returns whether the CSV is a codelist.

    :param csv.DictReader reader: A CSV reader
    """
    return 'Code' in reader.fieldnames  # TODO


def is_json_schema(data):
    """
    Returns whether the JSON data is a JSON Schema.

    :param data: JSON data
    """
    return '$schema' in data or 'definitions' in data or 'properties' in data


def is_json_merge_patch(data):
    """
    Returns whether the JSON data is a JSON Merge Patch.

    :param data: JSON data
    """
    return '$schema' not in data and ('definitions' in data or 'properties' in data)


def is_array_of_objects(field):
    """
    Returns whether a field is an array of objects.

    :param dict field: the field
    """
    return 'array' in field.get('type', []) and any(key in field.get('items', {}) for key in ('$ref', 'properties'))


def get_types(field):
    """
    Returns a field's ``type`` as a list.

    :param dict field: the field
    """
    if 'type' not in field:
        return []
    if isinstance(field['type'], str):
        return [field['type']]
    return field['type']


class RejectingDict(UserDict):
    """
    A ``dict`` that raises an error if a key is set more than once.
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
