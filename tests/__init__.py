import json
from pathlib import Path


def path(filename):
    return Path("tests") / "fixtures" / filename


def read(filename):
    return path(filename).read_text()


def parse(filename):
    with path(filename).open() as f:
        return json.load(f)
