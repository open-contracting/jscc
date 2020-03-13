import json
import os
import re
import warnings

from jsonref import JsonRef, JsonRefError
from jsonschema import FormatChecker
from jsonschema.validators import Draft4Validator as validator

from jscc.exceptions import DuplicateKeyError
from jscc.testing.schema import get_types, is_array_of_objects, traverse
from jscc.testing.traversal import walk, walk_csv_data, walk_json_data
from jscc.testing.util import difference, false, is_codelist, rejecting_dict, tracked, true

# The codelists defined in `standard/schema/codelists`. XXX Hardcoding.
external_codelists = {
}

exceptional_extensions = (
)

cwd = os.getcwd()
repo_name = os.path.basename(os.environ.get('TRAVIS_REPO_SLUG', cwd))
is_profile = os.path.isfile(os.path.join(cwd, 'Makefile')) and repo_name not in ('standard', 'infrastructure')
is_extension = os.path.isfile(os.path.join(cwd, 'extension.json')) or is_profile


def get_empty_files(include=true, parse_as_json=false):
    """
    Yields the path (as a tuple) of any file that is empty.

    If the file's contents are parsed as JSON, it is empty if the JSON is falsy. Otherwise, the file is empty if it
    contains only whitespace.

    :param function include: A method that accepts a file path and file name, and returns whether to test the file
                             (default true).

    pytest example::

        from jscc.testing.checks import get_empty_files
        from jscc.testing.util import warn_and_assert

        def test_empty():
            warn_and_assert(get_empty_files(), '{0} is empty, run: rm {0}',
                            'Files are empty. See warnings below.')

    """
    for path, name in walk():
        if tracked(path) and include(path, name) and name != '__init__.py':
            try:
                with open(path) as f:
                    text = f.read()
            except UnicodeDecodeError:
                continue  # the file is non-empty, and might be binary

            if name.endswith('.json'):
                try:
                    if not json.loads(text):
                        yield path,
                except json.decoder.JSONDecodeError:
                    continue  # the file is non-empty
            elif not text.strip():
                yield path,


def get_unindented_files(include=true):
    """
    Yields the path (as a tuple) of any JSON file that isn't formatted for humans.

    :param function include: A method that accepts a file path and file name, and returns whether to test the file
                             (default true).

    pytest example::

        from jscc.testing.checks import get_unindented_files
        from jscc.testing.util import warn_and_assert

        def test_indent():
            warn_and_assert(get_unindented_files(), '{0} is not indented as expected, run: ocdskit indent {0}',
                            'Files are not indented as expected. See warnings below, or run: ocdskit indent -r .')
    """
    for path, name, text, data in walk_json_data():
        if tracked(path) and include(path, name):
            expected = json.dumps(data, ensure_ascii=False, indent=2, separators=(',', ': ')) + '\n'
            if text != expected:
                yield path,


def get_invalid_json_files():
    """
    Yields the path and exception (as a tuple) of any JSON file that isn't valid.

    pytest example::

        from jscc.testing.checks import get_invalid_json_files
        from jscc.testing.util import warn_and_assert

        def test_indent():
            warn_and_assert(get_invalid_json_files(), '{0} is not valid JSON: {1}',
                            'JSON files are invalid. See warnings below.')
    """
    for path, name in walk():
        if path.endswith('.json'):
            with open(path) as f:
                text = f.read()
                if text:
                    try:
                        json.loads(text, object_pairs_hook=rejecting_dict)
                    except (json.decoder.JSONDecodeError, DuplicateKeyError) as e:
                        yield path, e


def get_json_schema_errors(schema, metaschema):
    """
    Yields each error in the JSON Schema file.

    :param object schema: the schema to validate
    :param object metaschema: the metaschema against which to validate

    pytest example::

        import json
        import requests
        from jscc.testing.checks import get_json_schema_errors

        def test_schema_valid():
            metaschema = requests.get('http://json-schema.org/draft-04/schema').json()

            path = 'schema/package.json'
            with open(path) as f:
                data = json.load(f)

            errors = list(get_json_schema_errors(data, metaschema))

            for error in errors:
                warnings.warn(json.dumps(error.instance, indent=2, separators=(',', ': ')))
                warnings.warn('ERROR: {0} ({1})\\n'.format(error.message, '/'.join(error.absolute_schema_path)))

            assert not errors, '{0} is not valid JSON Schema ({1} errors)'.format(path, len(errors))
    """
    for error in validator(metaschema, format_checker=FormatChecker()).iter_errors(schema):
        yield error


def validate_letter_case(*args):
    """
    Prints and returns the number of errors relating to the letter case of properties and definitions.
    """
    properties_exceptions = {'former_value'}  # deprecated
    definition_exceptions = {'record'}  # 2.0 fix

    def block(path, data, pointer):
        errors = 0

        parent = pointer.rsplit('/', 1)[-1]

        if parent == 'properties':
            for key in data.keys():
                if not re.search(r'^[a-z][A-Za-z]+$', key) and key not in properties_exceptions:
                    errors += 1
                    warnings.warn('ERROR: {} {}/{} should be lowerCamelCase ASCII letters'.format(path, pointer, key))
        elif parent == 'definitions':
            for key in data.keys():
                if not re.search(r'^[A-Z][A-Za-z]+$', key) and key not in definition_exceptions:
                    errors += 1
                    warnings.warn('ERROR: {} {}/{} should be UpperCamelCase ASCII letters'.format(path, pointer, key))

        return errors

    return traverse(block)(*args)


def validate_title_description_type(*args):  # OCDS-only
    """
    Prints and returns the number of errors relating to metadata in a JSON Schema.
    """
    schema_fields = ('definitions', 'deprecated', 'items', 'patternProperties', 'properties')
    schema_sections = ('patternProperties',)
    required_fields = ('title', 'description')

    def block(path, data, pointer):
        errors = 0

        parts = pointer.rsplit('/')
        if len(parts) >= 3:
            grandparent = parts[-2]
        else:
            grandparent = None
        parent = parts[-1]

        # Look for metadata fields on user-defined objects only. (Add exceptional condition for "items" field.)
        if parent not in schema_fields and grandparent not in schema_sections or grandparent == 'properties':
            for field in required_fields:
                # If a field has `$ref`, then its `title` and `description` might defer to the reference.
                # Exceptionally, the ocds_api_extension has a concise links section.
                if (field not in data or not data[field] or not data[field].strip()) and '$ref' not in data and 'links' not in parts:  # noqa
                    errors += 1
                    warnings.warn('ERROR: {} is missing {}/{}'.format(path, pointer, field))

            if 'type' not in data and '$ref' not in data and 'oneOf' not in data:
                errors += 1
                warnings.warn('ERROR: {0} is missing {1}/type or {1}/$ref or {1}/oneOf'.format(path, pointer))

        return errors

    return traverse(block)(*args)


def validate_null_type(path, data, pointer='', allow_null=True, should_be_nullable=True):  # OCDS-only
    """
    Prints and returns the number of errors relating to non-nullable optional fields and nullable required fields.
    """
    errors = 0

    null_exceptions = {
        '/definitions/Amendment/properties/changes/items/properties/property',  # deprecated

        # API extension adds metadata fields to which this rule doesn't apply.
        '/properties/packageMetadata',
        '/properties/packageMetadata/properties/uri',
        '/properties/packageMetadata/properties/publishedDate',
        '/properties/packageMetadata/properties/publisher',

        # 2.0 fixes.
        # See https://github.com/open-contracting/standard/issues/650
        '/definitions/Organization/properties/id',
        '/definitions/OrganizationReference/properties/id',
        '/definitions/RelatedProcess/properties/id',
        # Core extensions.
        '/definitions/ParticipationFee/properties/id',
        '/definitions/Lot/properties/id',
        '/definitions/LotGroup/properties/id',
    }
    non_null_exceptions = {
        '/definitions/LotDetails',  # actually can be null
    }
    object_null_exceptions = {
        '/definitions/Organization/properties/details',
        '/definitions/Amendment/properties/changes/items/properties/former_value',
    }

    if not allow_null:
        should_be_nullable = False

    if isinstance(data, list):
        for index, item in enumerate(data):
            errors += validate_null_type(path, item, pointer='{}/{}'.format(pointer, index), allow_null=allow_null)
    elif isinstance(data, dict):
        if 'type' in data and pointer:
            nullable = 'null' in data['type']
            # Objects should not be nullable.
            if 'object' in data['type'] and 'null' in data['type'] and pointer not in object_null_exceptions:
                errors += 1
                warnings.warn('ERROR: {}: nullable object {} at {}'.format(path, data['type'], pointer))
            if should_be_nullable:
                # A special case: If it's not required (should be nullable), but isn't nullable, it's okay if and only
                # if it's an object or an array of objects/references.
                if not nullable and data['type'] != 'object' and not is_array_of_objects(data) and pointer not in null_exceptions:  # noqa
                    errors += 1
                    warnings.warn('ERROR: {}: non-nullable optional {} at {}'.format(path, data['type'], pointer))
            elif nullable and pointer not in non_null_exceptions:
                errors += 1
                warnings.warn('ERROR: {}: nullable required {} at {}'.format(path, data['type'], pointer))

        required = data.get('required', [])

        for key, value in data.items():
            if key == 'properties':
                for k, v in data[key].items():
                    errors += validate_null_type(path, v, pointer='{}/{}/{}'.format(pointer, key, k),
                                                 allow_null=allow_null, should_be_nullable=k not in required)
            elif key == 'definitions':
                for k, v in data[key].items():
                    errors += validate_null_type(path, v, pointer='{}/{}/{}'.format(pointer, key, k),
                                                 allow_null=allow_null, should_be_nullable=False)
            elif key == 'items':
                errors += validate_null_type(path, data[key], pointer='{}/{}'.format(pointer, key),
                                             allow_null=allow_null, should_be_nullable=False)
            else:
                errors += validate_null_type(path, value, pointer='{}/{}'.format(pointer, key), allow_null=allow_null)

    return errors


def validate_codelist_enum(*args):  # OCDS-only
    """
    Prints and returns the number of errors relating to codelists in a JSON Schema.
    """
    enum_exceptions = {
        '/properties/tag',
        '/properties/initiationType',
    }

    def block(path, data, pointer):
        errors = 0

        parent = pointer.rsplit('/', 1)[-1]

        cached_types = {
            '/definitions/Metric/properties/id': ['string'],
            '/definitions/Milestone/properties/code': ['string', 'null'],
        }

        if 'codelist' in data:
            if 'type' not in data:  # e.g. if changing an existing property
                types = cached_types.get(pointer, ['array'])
            else:
                types = get_types(data)

            if data['openCodelist']:
                if ('string' in types and 'enum' in data or 'array' in types and 'enum' in data['items']):
                    # Open codelists shouldn't set `enum`.
                    errors += 1
                    warnings.warn('ERROR: {} must not set `enum` for open codelist at {}'.format(path, pointer))
            else:
                if 'string' in types and 'enum' not in data or 'array' in types and 'enum' not in data['items']:
                    # Fields with closed codelists should set `enum`.
                    errors += 1
                    warnings.warn('ERROR: {} must set `enum` for closed codelist at {}'.format(path, pointer))

                    actual = None
                elif 'string' in types:
                    actual = set(data['enum'])
                else:
                    actual = set(data['items']['enum'])

                # It'd be faster to cache the CSVs, but most extensions have only one closed codelist.
                for csvpath, csvname, reader in walk_csv_data():
                    # The codelist's CSV file should exist.
                    if csvname == data['codelist']:
                        # The codelist's CSV file should match the `enum` values, if the field is set.
                        if actual:
                            expected = set([row['Code'] for row in reader])

                            # Add None if the field is nullable.
                            if 'string' in types and 'null' in types:
                                expected.add(None)

                            if actual != expected:
                                added, removed = difference(actual, expected)

                                errors += 1
                                warnings.warn('ERROR: {} has mismatch between `enum` and codelist at {}{}{}'.format(
                                    path, pointer, added, removed))

                        break
                else:
                    # When validating a patched schema, the above code will fail to find the core codelists in an
                    # extension, but that is not an error. This duplicates a test in `validate_json_schema`.
                    if is_extension and data['codelist'] not in external_codelists:
                        errors += 1
                        warnings.warn('ERROR: {} is missing codelist: {}'.format(path, data['codelist']))
        elif 'enum' in data and parent != 'items' or 'items' in data and 'enum' in data['items']:
            # Exception: This profile overwrites `enum`.
            if repo_name not in exceptional_extensions or pointer not in enum_exceptions:
                # Fields with `enum` should set closed codelists.
                errors += 1
                warnings.warn('ERROR: {} has `enum` without codelist at {}'.format(path, pointer))

        return errors

    return traverse(block)(*args)


def validate_items_type(path, data, additional_valid_types=None):
    """
    Prints and returns the number of errors relating to the `type` of `items`.
    """
    exceptions = {
        '/definitions/Amendment/properties/changes/items',  # deprecated
        '/definitions/AmendmentUnversioned/properties/changes/items',  # deprecated
        '/definitions/record/properties/releases/oneOf/0/items',  # `type` is `object`
    }

    valid_types = {
        'array',
        'number',
        'string',
    }
    if additional_valid_types:
        valid_types.update(additional_valid_types)

    def block(path, data, pointer):
        errors = 0

        parent = pointer.rsplit('/', 1)[-1]

        if parent == 'items' and 'type' in data:
            types = get_types(data)

            invalid_type = next((_type for _type in types if _type not in valid_types), None)

            if invalid_type and pointer not in exceptions:
                errors += 1
                warnings.warn('ERROR: {} {} is an invalid `items` `type` at {}'.format(path, invalid_type, pointer))

        return errors

    return traverse(block)(path, data)


def validate_deep_properties(*args):
    """
    Prints warnings relating to deep objects, which, if appropriate, should be modeled as new definitions.
    """
    exceptions = {
        '/definitions/Amendment/properties/changes/items',  # deprecated
    }
    if is_extension:
        exceptions.add('/definitions/Item/properties/unit')  # avoid repetition in extensions

    def block(path, data, pointer):
        parts = pointer.rsplit('/', 2)
        if len(parts) == 3:
            grandparent = parts[-2]
        else:
            grandparent = None

        if pointer and grandparent != 'definitions' and 'properties' in data and pointer not in exceptions:
            warnings.warn('{} has deep properties at {}'.format(path, pointer))

        return 0

    return traverse(block)(*args)


def validate_object_id(*args):  # OCDS-only
    """
    Prints and returns the number of errors relating to objects within arrays lacking `id` fields.
    """
    exceptions = {
        'changes',  # deprecated
        'records',  # uses `ocid` not `id`
        '0',  # linked releases
    }

    required_id_exceptions = {
        # 2.0 fixes.
        # See https://github.com/open-contracting/standard/issues/650
        '/definitions/Amendment',
        '/definitions/Organization',
        '/definitions/OrganizationReference',
        '/definitions/RelatedProcess',
        '/definitions/Lot',
        '/definitions/LotGroup',
        '/definitions/ParticipationFee',
        # See https://github.com/open-contracting/ocds-extensions/issues/83
        '/definitions/Enquiry',
    }

    if repo_name == 'infrastructure':
        required_id_exceptions.add('/definitions/Classification')

    def block(path, data, pointer):
        errors = 0

        parts = pointer.split('/')
        parent = parts[-1]

        # If it's an array of objects.
        if ('type' in data and 'array' in data['type'] and 'properties' in data.get('items', {}) and
                parent not in exceptions and 'versionedRelease' not in parts):
            required = data['items'].get('required', [])

            if hasattr(data['items'], '__reference__'):
                original = data['items'].__reference__['$ref'][1:]
            else:
                original = pointer

            # See https://standard.open-contracting.org/latest/en/schema/merging/#whole-list-merge
            if 'id' not in data['items']['properties'] and not data.get('wholeListMerge'):
                errors += 1
                if original == pointer:
                    warnings.warn('ERROR: {} object array has no `id` property at {}'.format(path, pointer))
                else:
                    warnings.warn('ERROR: {} object array has no `id` property at {} (from {})'.format(
                        path, original, pointer))

            if 'id' not in required and not data.get('wholeListMerge') and original not in required_id_exceptions:
                errors += 1
                if original == pointer:
                    warnings.warn('ERROR: {} object array should require `id` property at {}'.format(path, pointer))
                else:
                    warnings.warn('ERROR: {} object array should require `id` property at {} (from {})'.format(
                        path, original, pointer))

        return errors

    return traverse(block)(*args)


def validate_merge_properties(*args):
    nullable_exceptions = {
        '/definitions/Amendment/properties/changes/items/properties/former_value',  # deprecated
        # See https://github.com/open-contracting/ocds-extensions/issues/83
        '/definitions/Tender/properties/enquiries',
    }

    def block(path, data, pointer):
        errors = 0

        types = get_types(data)

        if 'wholeListMerge' in data:
            if 'array' not in types:
                errors += 1
                warnings.warn('ERROR: {} `wholeListMerge` is set on non-array at {}'.format(path, pointer))
            if 'null' in types:
                errors += 1
                warnings.warn('ERROR: {} `wholeListMerge` is set on nullable at {}'.format(path, pointer))
        elif is_array_of_objects(data) and 'null' in types and pointer not in nullable_exceptions:
            errors += 1
            warnings.warn('ERROR: {} array should be `wholeListMerge` instead of nullable at {}'.format(path, pointer))

        if data.get('omitWhenMerged') and data.get('wholeListMerge'):
            errors += 1
            warnings.warn('ERROR: {} both `omitWhenMerged` and `wholeListMerge` are set at {}'.format(path, pointer))

        return errors

    return traverse(block)(*args)


def validate_ref(path, data):  # OCDS-only
    ref = JsonRef.replace_refs(data)

    try:
        # `repr` causes the references to be loaded, if possible.
        repr(ref)
    except JsonRefError as e:
        warnings.warn('ERROR: {} has {} at {}'.format(path, e.message, '/'.join(e.path)))
        return 1

    return 0


def validate_codelist_files_used_in_schema(path, data, top, is_extension):  # OCDS-only
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

    errors = 0

    # Extensions aren't expected to repeat referenced codelist CSV files.
    # TODO: This code assumes each schema uses all codelists. So, for now, skip package schema.
    codelist_files = set()
    for csvpath, csvname, reader in walk_csv_data(top=top):
        parts = csvpath.replace(top, '').split(os.sep)  # maybe inelegant way to isolate consolidated extension
        if is_codelist(reader) and (
                # Take all codelists in extensions.
                (is_extension and not is_profile) or
                # Take non-extension codelists in core, and non-core codelists in profiles.
                not any(c in parts for c in ('extensions', 'patched'))):
            if csvname.startswith(('+', '-')):
                if csvname[1:] not in external_codelists:
                    errors += 1
                    warnings.warn('ERROR: {} {} modifies non-existent codelist'.format(path, csvname))
            else:
                codelist_files.add(csvname)

    codelist_values = collect_codelist_values(path, data)
    if is_extension:
        all_codelist_files = codelist_files | external_codelists
    else:
        all_codelist_files = codelist_files

    unused_codelists = [codelist for codelist in codelist_files if codelist not in codelist_values]
    missing_codelists = [codelist for codelist in codelist_values if codelist not in all_codelist_files]

    if unused_codelists:
        errors += 1
        warnings.warn('ERROR: {} has unused codelists: {}'.format(path, ', '.join(unused_codelists)))
    if missing_codelists:
        errors += 1
        warnings.warn('ERROR: repository is missing codelists: {}'.format(', '.join(missing_codelists)))

    return errors


def validate_json_schema(path, name, data, schema, full_schema=not is_extension, top=cwd):
    """
    Prints and asserts errors in a JSON Schema.
    """
    errors = 0

    # Non-OCDS schema don't:
    # * pair "enum" and "codelist"
    # * disallow "null" in "type" of "items"
    # * UpperCamelCase definitions and lowerCamelCase properties
    # * allow "null" in the "type" of optional fields
    # * include "id" fields in objects within arrays
    # * require "title", "description" and "type" properties
    json_schema_exceptions = {
        'json-schema-draft-4.json',
        'meta-schema.json',
        'meta-schema-patch.json',
    }
    ocds_schema_exceptions = {
        'codelist-schema.json',
        'extension-schema.json',
        'extensions-schema.json',
        'extension_versions-schema.json',
        'dereferenced-release-schema.json',
    }
    exceptions = json_schema_exceptions | ocds_schema_exceptions
    allow_null = repo_name != 'infrastructure'

    if name not in exceptions:
        kwargs = {}
        if 'versioned-release-validation-schema.json' in path:
            kwargs['additional_valid_types'] = ['object']
        errors += validate_items_type(path, data, **kwargs)
        errors += validate_codelist_enum(path, data)
        errors += validate_letter_case(path, data)
        errors += validate_merge_properties(path, data)

    # `full_schema` is set to not expect extensions to repeat information from core.
    if full_schema:
        exceptions_plus_versioned = exceptions | {
            'versioned-release-validation-schema.json',
        }

        exceptions_plus_versioned_and_packages = exceptions_plus_versioned | {
            'project-package-schema.json',
            'record-package-schema.json',
            'release-package-schema.json',
            'project-package-schema.json',
        }

        # Extensions aren't expected to repeat referenced `definitions`.
        errors += validate_ref(path, data)

        if name not in exceptions_plus_versioned:
            # Extensions aren't expected to repeat `title`, `description`, `type`.
            errors += validate_title_description_type(path, data)
            # Extensions aren't expected to repeat referenced `definitions`.
            errors += validate_object_id(path, JsonRef.replace_refs(data))

        if name not in exceptions_plus_versioned_and_packages:
            # Extensions aren't expected to repeat `required`. Packages don't have merge rules.
            errors += validate_null_type(path, data, allow_null=allow_null)

            errors += validate_codelist_files_used_in_schema(path, data, top, is_extension)

    else:
        errors += validate_deep_properties(path, data)

    assert errors == 0, 'One or more JSON Schema files are invalid. See warnings below.'
