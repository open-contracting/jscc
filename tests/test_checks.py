import contextlib
import json
import os

from jscc.exceptions import DuplicateKeyError
from jscc.testing.checks import get_empty_files, get_invalid_json_files, get_misindented_files

from tests import path


@contextlib.contextmanager
def chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


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
