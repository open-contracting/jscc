import csv
import json

import pytest

from jscc.exceptions import DuplicateKeyError
from jscc.testing.schema import (get_types, is_array_of_objects, is_codelist, is_json_merge_patch, is_json_schema,
                                 is_property_missing, rejecting_dict)
from tests import parse, path


@pytest.mark.parametrize('filename,expected', [
    ('codelist.csv', True),
    ('data.csv', False),
])
def test_is_codelist(filename, expected):
    with open(path(filename)) as f:
        reader = csv.DictReader(f)

        assert is_codelist(reader) == expected


@pytest.mark.parametrize('filename,expected', [
    ('schema.json', True),
    ('patch.json', True),
])
def test_is_json_schema(filename, expected):
    assert is_json_schema(parse(filename)) == expected


@pytest.mark.parametrize('filename,expected', [
    ('schema.json', False),
    ('patch.json', True),
])
def test_is_json_merge_patch(filename, expected):
    assert is_json_merge_patch(parse(filename)) == expected


@pytest.mark.parametrize('field,expected', [
    ('arrayProperties', True),
    ('arrayRef', True),
    ('arrayType', False),
])
def test_is_array_of_objects(field, expected):
    assert is_array_of_objects(parse('schema.json')['properties'][field]) == expected


@pytest.mark.parametrize('prop,expected', [
    ('title', True),
    ('description', True),
    ('type', True),
    ('items', True),
    ('default', True),
    ('minimum', False),
    ('maximum', False),
    ('additionalItems', False),
])
def test_is_property_missing(prop, expected):
    assert is_property_missing(parse('schema.json')['properties']['metadata'], prop) == expected


@pytest.mark.parametrize('field,expected', [
    ('metadata', []),
    ('arrayProperties', ['array']),
    ('mixed', ['string', 'null']),
])
def test_get_types(field, expected):
    assert get_types(parse('schema.json')['properties'][field]) == expected


def test_rejecting_dict():
    with pytest.raises(DuplicateKeyError) as excinfo:
        json.loads('{"x": 0, "x": 1}', object_pairs_hook=rejecting_dict)

    assert str(excinfo.value) == 'x'
