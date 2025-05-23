"""Methods for interacting with or reasoning about the filesystem."""

import csv
import json
import os
from fnmatch import fnmatch
from io import StringIO

untracked = {
    '*.egg-info',
    '.tox',
    '.ve',
    '.venv',
    'htmlcov',
    'node_modules',
    'vendor',
}


def walk(top=None, excluded=('.git', '.ve', '.venv', '_static', 'build', 'fixtures')):
    """
    Walk a directory tree, and yield tuples consistent of a file path and file name, excluding Git files and
    third-party files under virtual environment, static, build, and test fixture directories (by default).

    :param str top: the file path of the directory tree
    :param tuple exclude: override the directories to exclude
    """
    if not top:
        top = os.getcwd()

    for root, dirs, files in os.walk(top):
        for directory in excluded:
            if directory in dirs:
                dirs.remove(directory)
        for name in files:
            yield os.path.join(root, name), name


def walk_json_data(patch=None, **kwargs):
    """
    Walk a directory tree, and yield tuples consisting of a file path, file name, text content, and JSON data.

    Accepts the same keyword arguments as :meth:`jscc.testing.filesystem.walk`.

    :param function patch: a method that accepts text, and returns modified text.
    """
    for path, name in walk(**kwargs):
        if path.endswith('.json'):
            with open(path) as f:
                text = f.read()
                if text:
                    if patch:
                        text = patch(text)
                    try:
                        yield path, name, text, json.loads(text)
                    except json.JSONDecodeError:
                        continue


def walk_csv_data(**kwargs):
    """
    Walk a directory tree, and yield tuples consisting of a file path, file name, text content, fieldnames, and rows.

    Accepts the same keyword arguments as :meth:`jscc.testing.filesystem.walk`.
    """
    for path, name in walk(**kwargs):
        if path.endswith('.csv'):
            with open(path, newline='') as f:
                text = f.read()
                reader = csv.DictReader(StringIO(text))
                try:
                    fieldnames = reader.fieldnames
                    rows = list(reader)
                    yield (path, name, text, fieldnames, rows)
                except csv.Error:
                    continue


def tracked(path):
    """
    Return whether the path isn't typically untracked in Git repositories.

    :param str path: a file path
    """
    return not any(fnmatch(part, pattern) for pattern in untracked for part in path.split(os.sep))
