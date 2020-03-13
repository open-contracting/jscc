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


def traverse(block):
    """
    Implements common logic used by ``validate_*`` methods.
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
