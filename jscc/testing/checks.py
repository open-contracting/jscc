"""
This module offers ``get_*`` functions to check for empty files, misindented JSON files, and invalid JSON files. See
"pytest example" in each function's documentation for usage examples.

This module also offers ``validate_*`` methods to test JSON Schema. Each method's behavior is customizable, and not all
methods are relevant to all schema.

The typical usage is to first define a test method like so:

.. code-block:: python

   from jscc.testing.filesystem import walk_json_data
   from jscc.schema import is_json_schema
   from jscc.testing.util import http_get

   schemas = [(path, name, data) for path, name, _, data in walk_json_data() if is_json_schema(data)]
   metaschema = http_get('http://json-schema.org/draft-04/schema').json()

   @pytest.mark.parametrize('path,name,data', schemas)
   def test_schema_valid(path, name, data):
       validate_json_schema(path, name, data, metaschema)

You can edit ``metaschema`` to be more strict and/or to add new properties. Then, define the ``validate_json_schema``
method that uses the ``validate_*`` methods. For example:

.. code-block:: python

   import jsonref
   from jscc.schema import (validate_array_items, validate_codelist_enum, validate_deep_properties,
                            validate_items_type, validate_letter_case, validate_merge_properties,
                            validate_metadata_presence, validate_null_type, validate_object_id, validate_ref,
                            validate_schema)

   def validate_json_schema(path, name, data, schema):
       errors = 0

       errors += validate_schema(path, data, schema)
       errors += validate_array_items(path, data)
       errors += validate_items_type(path, data)
       errors += validate_codelist_enum(path, data)
       errors += validate_letter_case(path, data)
       errors += validate_merge_properties(path, data)
       errors += validate_ref(path, data)
       errors += validate_metadata_presence(path, data)
       errors += validate_object_id(path, jsonref.replace_refs(data))
       errors += validate_null_type(path, data)
       # Here, we don't add to `errors`, in order to not count these warnings as errors.
       validate_deep_properties(path, data)

       assert not errors, 'One or more JSON Schema files are invalid. See warnings below.'

You can monkeypatch ``warnings.formatwarning`` to customize and abbreviate the warning messages:

.. code-block:: python

   import os
   import warnings
   from jscc.exceptions import DeepPropertiesWarning

   cwd = os.getcwd()

   def formatwarning(message, category, filename, lineno, line=None):
       # Prefix warnings that count as errors with "ERROR: ".
       if category != DeepPropertiesWarning:
           message = 'ERROR: ' + message
       # Remove the path to the current working directory.
       return str(message).replace(cwd + os.sep, '')

   warnings.formatwarning = formatwarning
"""

# In this module, it would be simpler to use a tuple for each `pointer` keyword argument, especially when calculating
# the last component of the pointer (the "parent"). However, it's easier when *using* the module to write JSON Pointers
# as strings. Therefore, we use strings instead of tuples.

import csv
import json
import os
import re
from warnings import warn

import jsonref
from jsonschema import FormatChecker
from jsonschema.validators import Draft4Validator as validator

from jscc.exceptions import (CodelistEnumWarning, DeepPropertiesWarning, DuplicateKeyError, ItemsTypeWarning,
                             LetterCaseWarning, MergePropertiesWarning, MetadataPresenceWarning, NullTypeWarning,
                             ObjectIdWarning, RefWarning, SchemaCodelistsMatchWarning, SchemaWarning)
from jscc.schema import get_types, is_array_of_objects, is_codelist, is_missing_property, rejecting_dict
from jscc.testing.filesystem import tracked, walk, walk_csv_data, walk_json_data
from jscc.testing.util import difference


def _true(*args):
    """
    Returns ``True`` (used internally as a default method).
    """
    return True


def _false(*args):
    """
    Returns ``False`` (used internally as a default method).
    """
    return False


def get_empty_files(include=_true, **kwargs):
    """
    Yields the path (as a tuple) of any file that is empty.

    JSON files are empty if their parsed contents are empty (empty array, empty object, empty string or ``null``).
    Other files are empty if they contain whitespace only.

    :param function include: a method that accepts a file path and file name, and returns whether to test the file
                             (default true)

    pytest example::

        from jscc.testing.checks import get_empty_files
        from jscc.testing.util import warn_and_assert

        def test_empty():
            warn_and_assert(get_empty_files(), '{0} is empty, run: rm {0}',
                            'Files are empty. See warnings below.')

    """
    for path, name in walk(**kwargs):
        if tracked(path) and include(path, name) and name != '__init__.py':
            try:
                with open(path) as f:
                    text = f.read()
            except UnicodeDecodeError:
                continue  # the file is non-empty, and might be binary

            if not text.strip():
                yield path,
            elif name.endswith('.json'):
                try:
                    value = json.loads(text)
                    if not value and not isinstance(value, (bool, int, float)):
                        yield path,
                except json.decoder.JSONDecodeError:
                    continue  # the file is non-empty


def get_misindented_files(include=_true, **kwargs):
    """
    Yields the path (as a tuple) of any JSON file that isn't formatted for humans.

    JSON files must be indented with two spaces, mustn't escape non-ASCII characters (no ``\\uXXXX`` sequences), and
    must have a newline at end of file.

    :param function include: a method that accepts a file path and file name, and returns whether to test the file
                             (default true)

    pytest example::

        from jscc.testing.checks import get_misindented_files
        from jscc.testing.util import warn_and_assert

        def test_indent():
            warn_and_assert(get_misindented_files(), '{0} is not indented as expected, run: ocdskit indent {0}',
                            'Files are not indented as expected. See warnings below, or run: ocdskit indent -r .')
    """
    for path, name, text, data in walk_json_data(**kwargs):
        if tracked(path) and include(path, name):
            expected = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
            if text != expected:
                yield path,


def get_invalid_json_files(**kwargs):
    """
    Yields the path and exception (as a tuple) of any JSON file that isn't valid.

    JSON files must be parsed without error by the ``json`` module, and JSON objects mustn't have duplicate keys.

    See https://tools.ietf.org/html/rfc7493#section-2.3

    pytest example::

        from jscc.testing.checks import get_invalid_json_files
        from jscc.testing.util import warn_and_assert

        def test_invalid_json():
            warn_and_assert(get_invalid_json_files(), '{0} is not valid JSON: {1}',
                            'JSON files are invalid. See warnings below.')
    """
    for path, name in walk(**kwargs):
        if path.endswith('.json'):
            with open(path) as f:
                text = f.read()
                if text:
                    try:
                        json.loads(text, object_pairs_hook=rejecting_dict)
                    except (json.decoder.JSONDecodeError, DuplicateKeyError) as e:
                        yield path, e


def get_invalid_csv_files(**kwargs):
    """
    Yields the path and exception (as a tuple) of any CSV file that isn't valid.

    CSV files must be parsed without error by the ``csv`` module.

    pytest example::

        from jscc.testing.checks import get_invalid_csv_files
        from jscc.testing.util import warn_and_assert

        def test_invalid_csv():
            warn_and_assert(get_invalid_csv_files(), '{0} is not valid CSV: {1}',
                            'CSV files are invalid. See warnings below.')
    """
    for path, name in walk(**kwargs):
        if path.endswith('.csv'):
            with open(path, newline='') as f:
                try:
                    csv.DictReader(f)
                except csv.Error as e:
                    yield path, e


def validate_schema(path, data, schema):
    """
    Warns and returns the number of errors relating to JSON Schema validation.

    Uses the `jsonschema <https://python-jsonschema.readthedocs.io/>`__ module.

    :param object schema: the metaschema against which to validate
    :returns: the number of errors
    :rtype: int
    """
    errors = 0

    for error in validator(schema, format_checker=FormatChecker()).iter_errors(data):
        errors += 1
        warn(f"{json.dumps(error.instance, indent=2)}\n{error.message} ({'/'.join(error.absolute_schema_path)})\n",
             SchemaWarning)

    return errors


def validate_letter_case(*args, property_exceptions=(), definition_exceptions=()):
    """
    Warns and returns the number of errors relating to the letter case of properties and definitions.

    Property names must be lowerCamelCase. Definition names must be UpperCamelCase. All must be ASCII letters only.

    :param property_exceptions: property names to ignore
    :type property_exceptions: list, tuple or set
    :param definition_exceptions: definition names to ignore
    :type definition_exceptions: list, tuple or set
    :returns: the number of errors
    :rtype: int
    """
    def block(path, data, pointer):
        errors = 0

        parent = pointer.rsplit('/', 1)[-1]

        if parent == 'properties':
            for key in data.keys():
                if not re.search(r'^[a-z][A-Za-z]+$', key) and key not in property_exceptions:
                    errors += 1
                    warn(f"{path}: {pointer}/{key} field isn't lowerCamelCase ASCII letters", LetterCaseWarning)
        elif parent == 'definitions':
            for key in data.keys():
                if not re.search(r'^[A-Z][A-Za-z]+$', key) and key not in definition_exceptions:
                    errors += 1
                    warn(f"{path}: {pointer}/{key} block isn't UpperCamelCase ASCII letters", LetterCaseWarning)

        return errors

    return _traverse(block)(*args)


def validate_metadata_presence(*args, allow_missing=_false):
    """
    Warns and returns the number of errors relating to metadata in a JSON Schema.

    The root schema and each field must have `"type" <https://tools.ietf.org/html/draft-fge-json-schema-validation-00#section-5.5.2>`__,
    `"title" and "description" <https://tools.ietf.org/html/draft-fge-json-schema-validation-00#section-6.1>`__
    properties, unless it has a `"$ref" <https://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03>`__ property.

    :param function allow_missing: a method that accepts a JSON Pointer, and returns whether the field is allowed to
                                   not have a "title" or "description" property
    :returns: the number of errors
    :rtype: int
    """  # noqa: E501
    schema_fields = {'definitions', 'deprecated', 'items', 'patternProperties', 'properties'}
    schema_sections = {'patternProperties'}
    required_properties = {'title', 'description'}

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
            for prop in required_properties:
                # If a field has `$ref`, then its `title` and `description` might defer to the reference.
                if is_missing_property(data, prop) and '$ref' not in data and not allow_missing(pointer):
                    errors += 1
                    warn(f'{path} is missing "{prop}" at {pointer}', MetadataPresenceWarning)

            if 'type' not in data and '$ref' not in data and 'oneOf' not in data and not allow_missing(pointer):
                errors += 1
                warn(f'{path} is missing "type" or "$ref" or "oneOf" at {pointer}', MetadataPresenceWarning)

        return errors

    return _traverse(block)(*args)


def validate_null_type(path, data, pointer='', no_null=False, expect_null=True, allow_object_null=(),
                       allow_no_null=(), allow_null=()):
    """
    Warns and returns the number of errors relating to non-nullable optional fields and nullable required fields.

    If :code:`no_null` is ``True``, then "type" properties mustn't include "null".

    Otherwise, the "type" properties for objects and arrays of objects mustn't include "null". If a field is `required
    <https://tools.ietf.org/html/draft-fge-json-schema-validation-00#section-5.4.3>`__, then its "type" property
    mustn't include "null". If a field isn't required (and it isn't an object or array of objects), then its "type"
    property must include "null".

    :param bool no_null: whether the standard disallows "null" in the "type" property of any field
    :param bool expect_null: whether the field, in context, is expected to have "null" in its "type" property
    :param allow_object_null: JSON Pointers of fields whose "type" properties are allowed to include "object", "null"
    :type allow_object_null: list, tuple or set
    :param allow_no_null: JSON Pointers of fields whose "type" properties are allowed to exclude "null"
    :type allow_no_null: list, tuple or set
    :param allow_null: JSON Pointers of fields whose "type" properties are allowed to include "null"
    :type allow_null: list, tuple or set
    :returns: the number of errors
    :rtype: int
    """
    errors = 0

    kwargs = {
        'allow_object_null': allow_object_null,
        'allow_no_null': allow_no_null,
        'allow_null': allow_null,
    }

    if no_null:
        expect_null = False

    if isinstance(data, list):
        for index, item in enumerate(data):
            errors += validate_null_type(path, item, pointer=f'{pointer}/{index}', **kwargs, no_null=no_null)
    elif isinstance(data, dict):
        if 'type' in data and pointer:
            null_in_type = 'null' in data['type']
            null_not_allowed = 'object' in data['type'] or is_array_of_objects(data)
            # Objects and arrays of objects mustn't be nullable.
            if null_in_type and null_not_allowed and pointer not in allow_object_null:
                errors += 1
                warn(f'{path} includes "null" in "type" at {pointer}', NullTypeWarning)
            elif expect_null:
                if not null_in_type and not null_not_allowed and pointer not in allow_no_null:
                    errors += 1
                    warn(f'{path} is missing "null" in "type" at {pointer}', NullTypeWarning)
            elif null_in_type and pointer not in allow_null:
                errors += 1
                warn(f'{path} includes "null" in "type" at {pointer}', NullTypeWarning)

        required = data.get('required', [])

        for key, value in data.items():
            if key in ('properties', 'definitions'):
                for k, v in data[key].items():
                    expect_null = key == 'properties' and k not in required
                    errors += validate_null_type(path, v, pointer=f'{pointer}/{key}/{k}', **kwargs, no_null=no_null,
                                                 expect_null=expect_null)
            else:
                v = data['items'] if key == 'items' else value
                errors += validate_null_type(path, v, pointer=f'{pointer}/{key}', **kwargs, no_null=no_null,
                                             expect_null=key != 'items')

    return errors


def validate_codelist_enum(*args, fallback=None, allow_enum=_false, allow_missing=_false):
    """
    Warns and returns the number of errors relating to codelists in a JSON Schema.

    If a field has a "codelist" property but no "type" property (e.g. if the "codelist" property is being overwritten),
    then its "type" is assumed to be "array" unless a fallback "type" is provided via :code:`fallback`.

    If the "codelist" property is set:

    -  If the "openCodelist" property is set to ``true``, then the "enum" property mustn't be set.
    -  If the "openCodelist" property is set to ``false``, then the "enum" property must be set, its value must include
       ``null`` if the "type" property includes "null", and its value must match the codes in the codelist.

    If the "enum" property is set, then the "codelist" and "openCodelist" properties must be set.

    :param dict fallback: a dict in which keys are JSON Pointers and values are lists of "type" values
    :param function allow_enum: a method that accepts a JSON Pointer, and returns whether the field is allowed to set
                                the "enum" property without setting the "codelist" property
    :param function allow_missing: a method that accepts a codelist name, and returns whether the codelist file
                                   is allowed to be missing from the repository
    :returns: the number of errors
    :rtype: int
    """
    if not fallback:
        fallback = {}

    def block(path, data, pointer):
        errors = 0

        parent = pointer.rsplit('/', 1)[-1]

        if 'codelist' in data:
            if 'type' not in data:  # e.g. if changing an existing property
                types = fallback.get(pointer, ['array'])  # otherwise, assume "array"
            else:
                types = get_types(data)

            if data['openCodelist']:
                if ('string' in types and 'enum' in data or 'array' in types and 'enum' in data['items']):
                    errors += 1
                    warn(f'{path} sets "enum", though "openCodelist" is true, at {pointer}',
                         CodelistEnumWarning)
            else:
                if 'string' in types and 'enum' not in data or 'array' in types and 'enum' not in data['items']:
                    errors += 1
                    warn(f'{path} is missing "enum", though "openCodelist" is false, at {pointer}',
                         CodelistEnumWarning)

                    actual = None
                elif 'string' in types:
                    actual = set(data['enum'])
                else:
                    actual = set(data['items']['enum'])

                # It'd be faster to cache the CSVs, but most extensions have only one closed codelist.
                for _, csvname, _, _, rows in walk_csv_data():
                    # The codelist's CSV file must exist.
                    if csvname == data['codelist']:
                        if actual:
                            expected = {row['Code'] for row in rows}
                            if 'string' in types and 'null' in types:
                                expected.add(None)

                            if actual != expected:
                                added, removed = difference(actual, expected)

                                errors += 1
                                warn(f"{path}: {pointer}/enum doesn't match codelists/{data['codelist']}"
                                     f"{added}{removed}", CodelistEnumWarning)
                        break
                else:
                    # When validating a patched schema, the above code will fail to find the core codelists in an
                    # extension, but that is not an error. This overlaps with `validate_schema_codelists_match`.
                    if not allow_missing(data['codelist']):
                        errors += 1
                        warn(f"{path} refers to missing file codelists/{data['codelist']} at {pointer}",
                             CodelistEnumWarning)
        elif 'enum' in data and parent != 'items' or 'items' in data and 'enum' in data['items']:
            if not allow_enum(pointer):
                errors += 1
                warn(f'{path} is missing "codelist" and "openCodelist" at {pointer}', CodelistEnumWarning)

        return errors

    return _traverse(block)(*args)


def validate_array_items(*args, allow_invalid=()):
    """
    Warns and returns the number of errors relating to array fields without an "items" property.

    A field whose "type" property includes "array" must set the "items" property.

    :param allow_invalid: JSON Pointers of fields whose "items" properties are allowed to be missing
    :type allow_invalid: list, tuple or set
    :returns: the number of errors
    :rtype: int
    """
    def block(path, data, pointer):
        errors = 0

        if 'type' in data and 'array' in data['type'] and 'items' not in data and pointer not in allow_invalid:
            errors += 1
            warn(f'{path} is missing "items" at {pointer}', DeepPropertiesWarning)

        return errors

    return _traverse(block)(*args)


def validate_items_type(*args, additional_valid_types=None, allow_invalid=()):
    """
    Warns and returns the number of errors relating to the "type" property under an "items" property.

    The "type" property under an "items" property must only include "array" (e.g. for geometries), "number"
    (e.g. for coordinates) and/or "string".

    :param additional_valid_types: additional valid values of the "type" property under an "items" property
    :type additional_valid_types: list, tuple or set
    :param allow_invalid: JSON Pointers of fields whose "type" properties are allowed to include invalid values
    :type allow_invalid: list, tuple or set
    :returns: the number of errors
    :rtype: int
    """
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

        if parent == 'items':
            for _type in get_types(data):
                if _type not in valid_types and pointer not in allow_invalid:
                    errors += 1
                    warn(f'{path} includes "{_type}" in "items/type" at {pointer}', ItemsTypeWarning)

        return errors

    return _traverse(block)(*args)


def validate_deep_properties(*args, allow_deep=()):
    """
    Warns and returns the number of errors relating to deep objects.

    The schema must use "definitions" instead of nesting "properties".

    :param allow_deep: JSON Pointers of fields to ignore
    :type allow_deep: list, tuple or set
    :returns: the number of errors
    :rtype: int
    """
    def block(path, data, pointer):
        errors = 0

        parts = pointer.rsplit('/', 2)
        if len(parts) == 3:
            grandparent = parts[-2]
        else:
            grandparent = None

        if pointer and grandparent != 'definitions' and 'properties' in data and pointer not in allow_deep:
            errors += 1
            warn(f'{path} has "properties" within "properties" at {pointer}', DeepPropertiesWarning)

        return errors

    return _traverse(block)(*args)


def validate_object_id(*args, allow_missing=_false, allow_optional=()):
    """
    Warns and returns the number of errors relating to objects within arrays lacking "id" fields.

    If an array field's "wholeListMerge" and "omitWhenMerged" properties aren't set or are set to ``false`` or
    ``null``, then the object fields under it must have an "id" field, and the "id" field must be required.

    :param function allow_missing: a method that accepts a JSON Pointer, and returns whether the field is allowed to
                                   not have an "id" field
    :param allow_optional: JSON Pointers of fields whose "id" field is allowed to be optional
    :type allow_optional: list, tuple or set
    :returns: the number of errors
    :rtype: int
    """
    def block(path, data, pointer):
        errors = 0

        if data.get('wholeListMerge') or data.get('omitWhenMerged') or allow_missing(pointer):
            return errors

        # If it's an array of objects.
        if 'type' in data and 'array' in data['type'] and 'properties' in data.get('items', {}):
            required = data['items'].get('required', [])

            if hasattr(data['items'], '__reference__'):
                original = data['items'].__reference__['$ref'][1:]
            else:
                original = pointer

            # See https://standard.open-contracting.org/latest/en/schema/merging/#whole-list-merge
            if 'id' not in data['items']['properties']:
                errors += 1
                if original == pointer:
                    warn(f'{path} is missing "id" in "items/properties" at {pointer}', ObjectIdWarning)
                else:
                    warn(f'{path} is missing "id" in "items/properties" at {original} (from {pointer})',
                         ObjectIdWarning)
            elif 'id' not in required and original not in allow_optional:
                errors += 1
                if original == pointer:
                    warn(f'{path} is missing "id" in "items/required" at {pointer}', ObjectIdWarning)
                else:
                    warn(f'{path} is missing "id" in "items/required" at {original} (from {pointer})',
                         ObjectIdWarning)

        return errors

    return _traverse(block)(*args)


def validate_merge_properties(*args):
    """
    Warns and returns the number of errors relating to missing or extra merge properties.

    The "omitWhenMerged" and "wholeListMerge" properties mustn't both be set, and mustn't be set to ``false`` or
    ``null``. The "wholeListMerge" property must be set on non-nullable arrays of objects only.

    See https://standard.open-contracting.org/1.1/en/schema/merging/#whole-list-merge

    :returns: the number of errors
    :rtype: int
    """
    def block(path, data, pointer):
        errors = 0

        if 'omitWhenMerged' in data and not data['omitWhenMerged']:
            errors += 1
            warn(f'{path} sets "omitWhenMerged" to false or null at {pointer}', MergePropertiesWarning)
        if 'wholeListMerge' in data and not data['wholeListMerge']:
            errors += 1
            warn(f'{path} sets "wholeListMerge" to false or null at {pointer}', MergePropertiesWarning)
        elif 'wholeListMerge' in data:
            if not is_array_of_objects(data):
                errors += 1
                warn(f'{path} sets "wholeListMerge", though the field is not an array of objects, at {pointer}',
                     MergePropertiesWarning)
            if 'omitWhenMerged' in data:
                errors += 1
                warn(f'{path} sets both "omitWhenMerged" and "wholeListMerge" at {pointer}',
                     MergePropertiesWarning)

        return errors

    return _traverse(block)(*args)


def validate_ref(path, data):
    """
    Warns and returns ``1`` if not all ``$ref``'erences can be resolved.

    Uses the `jsonref <https://jsonref.readthedocs.io/>`__ module.

    :returns: ``0`` or ``1``
    :rtype: int
    """
    try:
        jsonref.replace_refs(data, lazy_load=False)
    except jsonref.JsonRefError as e:
        warn(f"{path} has {e.message} at {'/'.join(map(str, e.path))}", RefWarning)
        return 1

    return 0


def validate_schema_codelists_match(path, data, top, is_extension=False, is_profile=False, external_codelists=None):
    """
    Warns and returns the number of errors relating to mismatches between codelist files and codelist references from
    JSON Schema.

    All codelist filenames that don't start with ``+`` or ``-`` must match codelist references. All codelist references
    must match codelist filenames or be in :code:`external_codelists`. All codelist filenames that start with ``+`` or
    ``-`` must be in :code:`external_codelists`.

    :param str top: the file path of the directory tree
    :param bool is_extension: whether the repository is an extension or a profile
    :param bool is_profile: whether the repository is a profile (a collection of extensions)
    :param external_codelists: names of codelists defined by the standard
    :type external_codelists: list, tuple or set
    :returns: the number of errors
    :rtype: int
    """
    if not external_codelists:
        external_codelists = set()

    def collect_codelist_values(path, data, pointer=''):
        """
        Collects ``codelist`` values from JSON Schema.
        """
        codelists = set()

        if isinstance(data, list):
            for index, item in enumerate(data):
                codelists.update(collect_codelist_values(path, item, pointer=f'{pointer}/{index}'))
        elif isinstance(data, dict):
            if 'codelist' in data:
                codelists.add(data['codelist'])

            for key, value in data.items():
                codelists.update(collect_codelist_values(path, value, pointer=f'{pointer}/{key}'))

        return codelists

    errors = 0

    codelist_files = set()
    for csvpath, csvname, _, fieldnames, _ in walk_csv_data(top=top):
        parts = csvpath.replace(top, '').split(os.sep)  # maybe inelegant way to isolate consolidated extension
        # Take all codelists in extensions, all codelists in core, and non-core codelists in profiles.
        if is_codelist(fieldnames) and ((is_extension and not is_profile) or 'patched' not in parts):
            if csvname.startswith(('+', '-')):
                if csvname[1:] not in external_codelists:
                    errors += 1
                    warn(f'{csvname} patches unknown codelist', SchemaCodelistsMatchWarning)
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
        warn(f"unused codelists: {', '.join(sorted(unused_codelists))}", SchemaCodelistsMatchWarning)
    if missing_codelists:
        errors += 1
        warn(f"missing codelists: {', '.join(sorted(missing_codelists))}", SchemaCodelistsMatchWarning)

    return errors


def _traverse(block):
    """
    Implements common logic used by ``validate_*`` methods.
    """
    def method(path, data, pointer=''):
        errors = 0

        if isinstance(data, list):
            for index, item in enumerate(data):
                errors += method(path, item, pointer=f'{pointer}/{index}')
        elif isinstance(data, dict):
            errors += block(path, data, pointer)

            for key, value in data.items():
                errors += method(path, value, pointer=f'{pointer}/{key}')

        return errors

    return method
