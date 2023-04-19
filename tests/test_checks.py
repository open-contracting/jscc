import contextlib
import json
import os
import warnings

import jsonref
import pytest

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


def t(message):
    path, rest = message.split(' ', 1)
    return f"{path.replace('/', os.sep)} {rest}"


def validate(name, *args, **kwargs):
    filepath = os.path.join('schema', f'{name}.json')
    return getattr(jscc.testing.checks, 'validate_' + name)(path(filepath), parse(filepath), *args, **kwargs)


def test_get_empty_files():
    directory = os.path.realpath(path('empty')) + os.sep
    with chdir(directory):
        paths = set()
        for result in get_empty_files():
            paths.add(result[0].replace(directory, ''))

            assert len(result) == 1

        assert paths == {
            'empty-array.json',
            'empty-object.json',
            'empty-string.json',
            'null.json',
            'whitespace.json',
            'whitespace.txt',
        }


def test_get_misindented_files():
    directory = os.path.realpath(path('indent')) + os.sep
    with chdir(directory):
        paths = set()
        for result in get_misindented_files():
            paths.add(result[0].replace(directory, ''))

            assert len(result) == 1

        assert paths == {
            'ascii.json',
            'compact.json',
            'no-newline.json',
        }


def test_get_invalid_json_files():
    directory = os.path.realpath(path('json')) + os.sep
    with chdir(directory):
        results = {}
        for result in get_invalid_json_files():
            results[result[0].replace(directory, '')] = result[1]

            assert len(result) == 2

        assert len(results) == 2
        assert isinstance(results['duplicate-key.json'], DuplicateKeyError)
        assert isinstance(results['invalid.json'], json.decoder.JSONDecodeError)
        assert str(results['duplicate-key.json']) == 'x'
        assert str(results['invalid.json']) == 'Expecting property name enclosed in double quotes: line 2 column 1 (char 2)'  # noqa: E501


def test_get_invalid_csv_files():
    directory = os.path.realpath(path('csv'))
    with chdir(directory):
        results = {}
        for result in get_invalid_csv_files():
            results[result[0].replace(directory, '')] = result[1]

            assert len(result) == 2

        assert len(results) == 0


def test_validate_codelist_enum():
    directory = os.path.realpath(path('schema')) + os.sep
    with chdir(directory):
        with pytest.warns(UserWarning) as records:
            filepath = os.path.join(directory, 'codelist_enum.json')
            with open(filepath) as f:
                data = json.load(f)
            errors = validate_codelist_enum(filepath, data)

    assert sorted(str(record.message).replace(directory, '') for record in records) == [
        'codelist_enum.json is missing "codelist" and "openCodelist" at /properties/noCodelistArray',
        'codelist_enum.json is missing "codelist" and "openCodelist" at /properties/noCodelistString',
        'codelist_enum.json is missing "enum", though "openCodelist" is false, at /properties/failClosedArray',
        'codelist_enum.json is missing "enum", though "openCodelist" is false, at /properties/failClosedString',
        "codelist_enum.json refers to missing file codelists/missing.csv at /properties/missing",
        'codelist_enum.json sets "enum", though "openCodelist" is true, at /properties/failOpenArray',
        'codelist_enum.json sets "enum", though "openCodelist" is true, at /properties/failOpenString',
        "codelist_enum.json: /properties/mismatchArray/enum doesn't match codelists/test.csv; added {'extra'}",
        "codelist_enum.json: /properties/mismatchString/enum doesn't match codelists/test.csv; added {'extra'}; removed {None}",  # noqa: E501
    ]
    assert errors == len(records) == 9


def test_validate_deep_properties():
    with pytest.warns(UserWarning) as records:
        errors = validate('deep_properties', allow_deep={'/properties/allow'})

    assert sorted(str(record.message) for record in records) == [
        t('tests/fixtures/schema/deep_properties.json has "properties" within "properties" at /properties/parent'),
    ]
    assert errors == len(records) == 1


def test_validate_array_items():
    with pytest.warns(UserWarning) as records:
        errors = validate('array_items', allow_invalid={'/properties/allow'})

    assert sorted(str(record.message) for record in records) == [
        t('tests/fixtures/schema/array_items.json is missing "items" at /properties/fail'),
    ]
    assert errors == len(records) == 1


def test_validate_items_type():
    with pytest.warns(UserWarning) as records:
        errors = validate('items_type', additional_valid_types=['boolean'],
                          allow_invalid={'/properties/allow/items'})

    assert sorted(str(record.message) for record in records) == [
        t('tests/fixtures/schema/items_type.json includes "object" in "items/type" at /properties/fail/items'),
    ]
    assert errors == len(records) == 1


def test_validate_letter_case():
    with pytest.warns(UserWarning) as records:
        errors = validate('letter_case', property_exceptions={'Allow'}, definition_exceptions={'allow'})

    assert sorted(str(record.message) for record in records) == [
        t("tests/fixtures/schema/letter_case.json: /definitions/Fail_Phrase block isn't UpperCamelCase ASCII letters"),
        t("tests/fixtures/schema/letter_case.json: /definitions/fail block isn't UpperCamelCase ASCII letters"),
        t("tests/fixtures/schema/letter_case.json: /properties/Fail field isn't lowerCamelCase ASCII letters"),
        t("tests/fixtures/schema/letter_case.json: /properties/fail_phrase field isn't lowerCamelCase ASCII letters"),
    ]
    assert errors == len(records) == 4


def test_validate_merge_properties():
    with pytest.warns(UserWarning) as records:
        errors = validate('merge_properties')

    assert sorted(str(record.message) for record in records) == [
        t('tests/fixtures/schema/merge_properties.json sets "omitWhenMerged" to false or null at /properties/omitWhenMergedFalse'),  # noqa: E501
        t('tests/fixtures/schema/merge_properties.json sets "wholeListMerge" to false or null at /properties/wholeListMergeFalse'),  # noqa: E501
        t('tests/fixtures/schema/merge_properties.json sets "wholeListMerge", though the field is not an array of objects, at /properties/array'),  # noqa: E501
        t('tests/fixtures/schema/merge_properties.json sets both "omitWhenMerged" and "wholeListMerge" at /properties/both'),  # noqa: E501
    ]
    assert errors == len(records) == 4


def test_validate_metadata_presence():
    def allow_missing(pointer):
        return pointer == '/properties/allow'

    with pytest.warns(UserWarning) as records:
        errors = validate('metadata_presence', allow_missing=allow_missing)

    assert sorted(str(record.message) for record in records) == [
        t('tests/fixtures/schema/metadata_presence.json is missing "description" at /properties/fail'),
        t('tests/fixtures/schema/metadata_presence.json is missing "title" at /properties/fail'),
        t('tests/fixtures/schema/metadata_presence.json is missing "type" or "$ref" or "oneOf" at /properties/fail'),
    ]
    assert errors == len(records) == 3


def test_validate_null_type():
    with pytest.warns(UserWarning) as records:
        errors = validate('null_type')

    assert sorted(str(record.message) for record in records) == [
        t('tests/fixtures/schema/null_type.json includes "null" in "type" at /properties/failObject'),
        t('tests/fixtures/schema/null_type.json includes "null" in "type" at /properties/failObjectArray'),
        t('tests/fixtures/schema/null_type.json includes "null" in "type" at /properties/failRequired'),
        t('tests/fixtures/schema/null_type.json is missing "null" in "type" at /properties/failOptional'),
    ]
    assert errors == len(records) == 4


def test_validate_null_type_no_null():
    with pytest.warns(UserWarning) as records:
        errors = validate('null_type', no_null=True)

    assert sorted(str(record.message) for record in records) == [
        t('tests/fixtures/schema/null_type.json includes "null" in "type" at /properties/failObject'),
        t('tests/fixtures/schema/null_type.json includes "null" in "type" at /properties/failObjectArray'),
        t('tests/fixtures/schema/null_type.json includes "null" in "type" at /properties/failRequired'),
        t('tests/fixtures/schema/null_type.json includes "null" in "type" at /properties/passOptional'),
    ]
    assert errors == len(records) == 4


def test_validate_object_id():
    def allow_missing(pointer):
        return pointer == '/properties/allowMissing'

    filepath = os.path.join('schema', 'object_id.json')
    with pytest.warns(UserWarning) as records:
        errors = validate_object_id(path(filepath), jsonref.replace_refs(parse(filepath)), allow_missing=allow_missing,
                                    allow_optional='/properties/allowOptional')

    assert sorted(str(record.message) for record in records) == [
        t('tests/fixtures/schema/object_id.json is missing "id" in "items/properties" at /definitions/Missing (from /refMissing)'),  # noqa: E501
        t('tests/fixtures/schema/object_id.json is missing "id" in "items/properties" at /properties/missing'),
        t('tests/fixtures/schema/object_id.json is missing "id" in "items/required" at /definitions/Optional (from /refOptional)'),  # noqa: E501
        t('tests/fixtures/schema/object_id.json is missing "id" in "items/required" at /properties/optional'),
    ]
    assert errors == len(records) == 4


def test_validate_ref_pass():
    filepath = os.path.join('schema', 'schema.json')

    with warnings.catch_warnings():
        warnings.simplefilter('error')  # no warnings

        errors = validate_ref(path(filepath), parse(filepath))

    assert errors == 0


def test_validate_ref_fail():
    with pytest.warns(UserWarning) as records:
        errors = validate('ref')

    assert sorted(str(record.message) for record in records) == [
        t("tests/fixtures/schema/ref.json has Error while resolving `#/definitions/Fail`: Unresolvable JSON pointer: '/definitions/Fail' at properties/fail"),  # noqa: E501
    ]
    assert errors == len(records) == 1


def test_validate_schema():
    with pytest.warns(UserWarning) as records:
        errors = validate('schema', parse('meta-schema.json'))

    assert [str(record.message) for record in records] == [
        "[]\n[] is not of type 'object' (properties/properties/type)\n",
    ]
    assert errors == len(records) == 1


def test_validate_schema_codelists_match():
    filepath = os.path.join('schema', 'codelist_enum.json')
    with pytest.warns(UserWarning) as records:
        errors = validate_schema_codelists_match(path(filepath), parse(filepath), path('schema'))

    assert sorted(str(record.message) for record in records) == [
        '+nonexistent.csv patches unknown codelist',
        'missing codelists: failOpenArray.csv, failOpenString.csv, missing.csv',
        'unused codelists: extra.csv',
    ]
    assert errors == len(records) == 3


def test_validate_schema_codelists_match_codelist():
    filepath = os.path.join('schema', 'codelist_enum.json')
    with pytest.warns(UserWarning) as records:
        errors = validate_schema_codelists_match(path(filepath), parse(filepath), path('schema'), is_extension=True,
                                                 external_codelists={'failOpenArray.csv', 'failOpenString.csv'})

    assert sorted(str(record.message) for record in records) == [
        '+nonexistent.csv patches unknown codelist',
        'missing codelists: missing.csv',
        'unused codelists: extra.csv',
    ]
    assert errors == len(records) == 3
