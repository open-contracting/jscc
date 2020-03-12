import csv
import json
import os

cwd = os.getcwd()  # TODO


def walk(top=cwd, excluded=('.git', '.ve', '_static', 'build', 'fixtures')):
    """
    Walks a directory tree, and yields tuples consistent of a file path and file name, excluding Git files and
    third-party files under virtual environment, static, build, and test fixture directories (by default).

    :param str top: the file path of the directory tree
    :param tuple exclude: override the directories to exclude
    """
    for root, dirs, files in os.walk(top):
        for directory in excluded:
            if directory in dirs:
                dirs.remove(directory)
        for name in files:
            yield root, name


def walk_json_data(patch=None, **kwargs):
    """
    Walks a directory tree, and yields tuples consisting of a file path, text content, and JSON data.
    """
    for root, name in walk(**kwargs):
        if name.endswith('.json'):
            path = os.path.join(root, name)
            with open(path) as f:
                text = f.read()
                if text:
                    if patch:
                        text = patch(text)
                    try:
                        yield path, text, json.loads(text)
                    except json.decoder.JSONDecodeError:
                        continue


def walk_csv_data(**kwargs):
    """
    Walks a directory tree, and yields tuples consisting of a file path and CSV reader.
    """
    for root, name in walk(**kwargs):
        if name.endswith('.csv'):
            path = os.path.join(root, name)
            with open(path, newline='') as f:
                yield path, csv.DictReader(f)
