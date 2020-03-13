import json
import os.path


def path(filename):
    return os.path.join('tests', 'fixtures', filename)


def read(filename):
    with open(path(filename)) as f:
        return f.read()


def parse(filename):
    with open(path(filename)) as f:
        return json.load(f)
