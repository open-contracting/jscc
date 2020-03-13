"""
Methods for reading JSON Schema and CSV codelists.
"""
from collections import UserDict

from jscc.exceptions import DuplicateKeyError


def is_codelist(reader):
    """
    Returns whether the CSV is a codelist.

    :param csv.DictReader reader: A CSV reader
    """
    # OCDS uses titlecase. BODS uses lowercase.
    return 'Code' in reader.fieldnames or 'code' in reader.fieldnames


def is_json_schema(data):
    """
    Returns whether the JSON data is a JSON Schema.

    :param dict data: JSON data
    """
    return '$schema' in data or 'definitions' in data or 'properties' in data


def is_json_merge_patch(data):
    """
    Returns whether the JSON data is a JSON Merge Patch.

    :param dict data: JSON data
    """
    return '$schema' not in data and ('definitions' in data or 'properties' in data)


def is_array_of_objects(field):
    """
    Returns whether a field is an array of objects.

    :param dict field: the field
    """
    return 'array' in field.get('type', []) and any(key in field.get('items', {}) for key in ('$ref', 'properties'))


def is_property_missing(field, prop):
    """
    Returns whether a field's property isn't set, is empty, or is whitespace.

    :param dict field: the field
    :param str prop: the property
    """
    return prop not in field or not field[prop] and not isinstance(field[prop], (bool, int, float)) or \
        isinstance(field[prop], str) and not field[prop].strip()


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
