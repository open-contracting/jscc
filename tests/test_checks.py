import contextlib
import json
import os

import pytest
from jsonref import JsonRef

import jscc.testing.checks
from jscc.exceptions import DuplicateKeyError
from jscc.testing.checks import (get_empty_files, get_invalid_csv_files, get_invalid_json_files, get_misindented_files,
                                 validate_codelist_enum, validate_object_id, validate_ref,
                                 validate_schema_codelists_match)
from tests import parse, path


@contextlib.contextmanager
def chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def validate(name, *args, **kwargs):
    filepath = 'schema/{}.json'.format(name)
    return getattr(jscc.testing.checks, 'validate_' + name)(path(filepath), parse(filepath), *args, **kwargs)


def test_get_empty_files():
    directory = os.path.realpath(path('empty'))
    with chdir(directory):
        paths = set()
        for result in get_empty_files():
            paths.add(result[0].replace(directory, ''))

            assert len(result) == 1

        assert paths == {
            '/empty-array.json',
            '/empty-object.json',
            '/empty-string.json',
            '/null.json',
            '/whitespace.txt',
        }


def test_get_misindented_files():
    directory = os.path.realpath(path('indent'))
    with chdir(directory):
        paths = set()
        for result in get_misindented_files():
            paths.add(result[0].replace(directory, ''))

            assert len(result) == 1

        assert paths == {
            '/ascii.json',
            '/compact.json',
            '/no-newline.json',
        }


def test_get_invalid_json_files():
    directory = os.path.realpath(path('json'))
    with chdir(directory):
        results = {}
        for result in get_invalid_json_files():
            results[result[0].replace(directory, '')] = result[1]

            assert len(result) == 2

        assert len(results) == 2
        assert isinstance(results['/duplicate-key.json'], DuplicateKeyError)
        assert isinstance(results['/invalid.json'], json.decoder.JSONDecodeError)
        assert str(results['/duplicate-key.json']) == 'x'
        assert str(results['/invalid.json']) == 'Expecting property name enclosed in double quotes: line 2 column 1 (char 2)'  # noqa


def test_get_invalid_csv_files():
    directory = os.path.realpath(path('csv'))
    with chdir(directory):
        results = {}
        for result in get_invalid_csv_files():
            results[result[0].replace(directory, '')] = result[1]

            assert len(result) == 2

        assert len(results) == 0


def test_validate_codelist_enum():
    directory = os.path.realpath(path('schema'))
    with chdir(directory):
        with pytest.warns(UserWarning) as records:
            filepath = os.path.join(directory, 'codelist_enum.json')
            with open(filepath) as f:
                data = json.load(f)
            errors = validate_codelist_enum(filepath, data)

    assert errors == len(records) == 9
    assert sorted(str(record.message).replace(directory, '') for record in records) == [
        '/codelist_enum.json has "enum" without codelist at /properties/noCodelistArray',
        '/codelist_enum.json has "enum" without codelist at /properties/noCodelistString',
        '/codelist_enum.json has mismatch between "enum" and codelist at /properties/mismatchArray; added {\'extra\'}',
        '/codelist_enum.json has mismatch between "enum" and codelist at /properties/mismatchString; added {\'extra\'}; removed {None}',  # noqa
        '/codelist_enum.json is missing codelist: missing.csv',
        '/codelist_enum.json must not set "enum" for open codelist at /properties/failOpenArray',
        '/codelist_enum.json must not set "enum" for open codelist at /properties/failOpenString',
        '/codelist_enum.json must set "enum" for closed codelist at /properties/failClosedArray',
        '/codelist_enum.json must set "enum" for closed codelist at /properties/failClosedString',
    ]


def test_validate_deep_properties():
    with pytest.warns(UserWarning) as records:
        errors = validate('deep_properties', allow_deep={'/properties/allow'})

    assert errors == len(records) == 1
    assert sorted(str(record.message) for record in records) == [
        'tests/fixtures/schema/deep_properties.json has deep properties at /properties/parent',
    ]


def test_validate_items_type():
    with pytest.warns(UserWarning) as records:
        errors = validate('items_type', additional_valid_types=['boolean'],
                          allow_invalid={'/properties/allow/items'})

    assert errors == len(records) == 1
    assert sorted(str(record.message) for record in records) == [
        'tests/fixtures/schema/items_type.json "object" is an invalid "items" "type" at /properties/fail/items',
    ]


def test_validate_letter_case():
    with pytest.warns(UserWarning) as records:
        errors = validate('letter_case', property_exceptions={'Allow'}, definition_exceptions={'allow'})

    assert errors == len(records) == 4
    assert sorted(str(record.message) for record in records) == [
        'tests/fixtures/schema/letter_case.json /definitions/Fail_Phrase should be UpperCamelCase ASCII letters',  # noqa
        'tests/fixtures/schema/letter_case.json /definitions/fail should be UpperCamelCase ASCII letters',
        'tests/fixtures/schema/letter_case.json /properties/Fail should be lowerCamelCase ASCII letters',
        'tests/fixtures/schema/letter_case.json /properties/fail_phrase should be lowerCamelCase ASCII letters',
    ]


def test_validate_merge_properties():
    with pytest.warns(UserWarning) as records:
        errors = validate('merge_properties')

    assert errors == len(records) == 4
    assert sorted(str(record.message) for record in records) == [
        'tests/fixtures/schema/merge_properties.json "wholeListMerge" is set on non-array at /properties/string',  # noqa
        'tests/fixtures/schema/merge_properties.json "wholeListMerge" is set on nullable at /properties/nullable',  # noqa
        'tests/fixtures/schema/merge_properties.json array should be "wholeListMerge" instead of nullable at /properties/missing',  # noqa
        'tests/fixtures/schema/merge_properties.json both "omitWhenMerged" and "wholeListMerge" are set at /properties/both',  # noqa
    ]


def test_validate_metadata_presence():
    def allow_missing(pointer):
        return pointer == '/properties/allow'

    with pytest.warns(UserWarning) as records:
        errors = validate('metadata_presence', allow_missing=allow_missing)

    assert errors == len(records) == 3
    assert sorted(str(record.message) for record in records) == [
        'tests/fixtures/schema/metadata_presence.json is missing /properties/fail/description',
        'tests/fixtures/schema/metadata_presence.json is missing /properties/fail/title',
        'tests/fixtures/schema/metadata_presence.json is missing /properties/fail/type or /properties/fail/$ref or /properties/fail/oneOf',  # noqa
    ]


def test_validate_null_type():
    with pytest.warns(UserWarning) as records:
        errors = validate('null_type')

    assert errors == len(records) == 3
    assert sorted(str(record.message) for record in records) == [
        "tests/fixtures/schema/null_type.json non-nullable optional string at /properties/failOptional",
        "tests/fixtures/schema/null_type.json nullable object ['object', 'null'] at /properties/failObject",
        "tests/fixtures/schema/null_type.json nullable required ['string', 'null'] at /properties/failRequired",
    ]


def test_validate_null_type_no_null():
    with pytest.warns(UserWarning) as records:
        errors = validate('null_type', no_null=True)

    assert errors == len(records) == 3
    assert sorted(str(record.message) for record in records) == [
        "tests/fixtures/schema/null_type.json nullable object ['object', 'null'] at /properties/failObject",
        "tests/fixtures/schema/null_type.json nullable required ['string', 'null'] at /properties/failRequired",
        "tests/fixtures/schema/null_type.json nullable required ['string', 'null'] at /properties/passOptional",
    ]


def test_validate_object_id():
    def allow_missing(pointer):
        return pointer == '/properties/allowMissing'

    filepath = 'schema/object_id.json'
    with pytest.warns(UserWarning) as records:
        errors = validate_object_id(path(filepath), JsonRef.replace_refs(parse(filepath)), allow_missing=allow_missing,
                                    allow_optional='/properties/allowOptional')

    assert errors == len(records) == 4
    assert sorted(str(record.message) for record in records) == [
        'tests/fixtures/schema/object_id.json object array has no "id" field at /definitions/Missing (from /refMissing)',  # noqa
        'tests/fixtures/schema/object_id.json object array has no "id" field at /properties/missing',
        'tests/fixtures/schema/object_id.json object array should require "id" field at /definitions/Optional (from /refOptional)',  # noqa
        'tests/fixtures/schema/object_id.json object array should require "id" field at /properties/optional',
    ]


def test_validate_ref_pass():
    filepath = 'schema/schema.json'
    with pytest.warns(None) as records:
        errors = validate_ref(path(filepath), parse(filepath))

    assert errors == len(records) == 0


def test_validate_ref_fail():
    with pytest.warns(UserWarning) as records:
        errors = validate('ref')

    assert errors == len(records) == 1
    assert sorted(str(record.message) for record in records) == [
        "tests/fixtures/schema/ref.json has Unresolvable JSON pointer: '/definitions/Fail' at properties/fail",
    ]


def test_validate_schema():
    with pytest.warns(UserWarning) as records:
        errors = validate('schema', parse('meta-schema.json'))

    assert errors == len(records) == 1
    assert [str(record.message) for record in records] == [
        "[]\n[] is not of type 'object' (properties/properties/type)\n",
    ]


def test_validate_schema_codelists_match():
    filepath = 'schema/codelist_enum.json'
    with pytest.warns(UserWarning) as records:
        errors = validate_schema_codelists_match(path(filepath), parse(filepath), path('schema'))

    assert errors == len(records) == 3
    assert sorted(str(record.message) for record in records) == [
        '+nonexistent.csv modifies non-existent codelist',
        'missing codelists: failOpenArray.csv, failOpenString.csv, missing.csv',
        'unused codelists: extra.csv',
    ]


def test_validate_schema_codelists_match_codelist():
    filepath = 'schema/codelist_enum.json'
    with pytest.warns(UserWarning) as records:
        errors = validate_schema_codelists_match(path(filepath), parse(filepath), path('schema'), is_extension=True,
                                                 external_codelists={'failOpenArray.csv', 'failOpenString.csv'})

    assert errors == len(records) == 3
    assert sorted(str(record.message) for record in records) == [
        '+nonexistent.csv modifies non-existent codelist',
        'missing codelists: missing.csv',
        'unused codelists: extra.csv',
    ]
