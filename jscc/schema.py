"""
Methods for interacting with or reasoning about JSON Schema and CSV codelists.
"""
from collections import UserDict
from copy import deepcopy

import json_merge_patch

from jscc.exceptions import DuplicateKeyError
from jscc.testing.util import http_get


def is_codelist(fieldnames):
    """
    :param list fieldnames: the fieldnames of the CSV
    :returns: whether the CSV is a codelist
    :rtype: bool
    """
    # OCDS uses titlecase. BODS uses lowercase.
    return 'Code' in fieldnames or 'code' in fieldnames


def is_json_schema(data):
    """
    :param dict data: JSON data
    :returns: whether the JSON data is a JSON Schema
    :rtype: bool
    """
    return '$schema' in data or 'definitions' in data or 'properties' in data


def is_json_merge_patch(data):
    """
    :param dict data: JSON data
    :returns: whether the JSON data is a JSON Merge Patch
    :rtype: bool
    """
    return '$schema' not in data and ('definitions' in data or 'properties' in data)


def is_array_of_objects(field):
    """
    :param dict field: the field
    :returns: whether a field is an array of objects
    :rtype: bool
    """
    return 'array' in field.get('type', []) and any(key in field.get('items', {}) for key in ('$ref', 'properties'))


def is_missing_property(field, prop):
    """
    :param dict field: the field
    :param str prop: the property
    :returns: whether a field's property isn't set, is empty, or is whitespace
    :rtype: bool
    """
    return prop not in field or not field[prop] and not isinstance(field[prop], (bool, int, float)) or \
        isinstance(field[prop], str) and not field[prop].strip()


def get_types(field):
    """
    Returns a field's "type" as a list.

    :param dict field: the field
    :returns: a field's "type"
    :rtype: list
    """
    if 'type' not in field:
        return []
    if isinstance(field['type'], str):
        return [field['type']]
    return field['type']


def extend_schema(basename, schema, metadata, codelists=None):
    """
    Patches a JSON Schema with an extension's dependencies, recursively.

    If :code:`codelists` is provided, it will be updated with the codelists from the dependencies.

    :param str basename: the JSON Schema file's basename
    :param dict schema: the JSON Schema file's parsed contents
    :param dict metadata: the extension metadata file's parsed contents
    :param set codelists: any set
    :returns: the patched schema
    :rtype: dict
    """
    def recurse(metadata):
        urls = metadata.get('dependencies', []) + metadata.get('testDependencies', [])
        for metadata_url in urls:
            patch_url = f"{metadata_url.rsplit('/', 1)[0]}/{basename}"
            metadata = http_get(metadata_url).json()
            patch = http_get(patch_url).json()
            if codelists is not None:
                codelists.update(metadata.get('codelists', []))
            json_merge_patch.merge(patched, patch)
            recurse(metadata)

    patched = deepcopy(schema)
    recurse(metadata)

    return patched


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
