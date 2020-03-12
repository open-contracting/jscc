import csv
import json
import os
import re
from collections import UserDict

import requests

# Whether to use the 1.1-dev version of OCDS.
use_development_version = False

cwd = os.getcwd()

repo_name = os.path.basename(os.environ.get('TRAVIS_REPO_SLUG', cwd))

ocds_version = os.environ.get('OCDS_TEST_VERSION')

if repo_name == 'infrastructure':
    ocds_schema_base_url = 'https://standard.open-contracting.org/infrastructure/schema/'
else:
    ocds_schema_base_url = 'https://standard.open-contracting.org/schema/'
development_base_url = 'https://raw.githubusercontent.com/open-contracting/standard/1.1-dev/standard/schema'

ocds_tags = re.findall(r'\d+__\d+__\d+', requests.get(ocds_schema_base_url).text)
if ocds_version:
    ocds_tag = ocds_version.replace('.', '__')
else:
    ocds_tag = ocds_tags[-1]


class RejectingDict(UserDict):
    """
    Allows a key to be set at most once, in order to raise an error on duplicate keys in JSON.
    """
    def __setitem__(self, k, v):
        # See https://tools.ietf.org/html/rfc7493#section-2.3
        if k in self.keys():
            raise ValueError('Key set more than once {}'.format(k))
        else:
            return super().__setitem__(k, v)


def object_pairs_hook(pairs):
    rejecting_dict = RejectingDict(pairs)
    # We return the wrapped dict, not the RejectingDict itself, because jsonschema checks the type.
    return rejecting_dict.data


def walk(top=cwd):
    """
    Yields all files, except third-party files under virtual environment, static, build, and test fixture directories.
    """
    for root, dirs, files in os.walk(top):
        for directory in ('.git', '.ve', '_static', 'build', 'fixtures'):
            if directory in dirs:
                dirs.remove(directory)
        for name in files:
            yield (root, name)


def walk_json_data(top=cwd):
    """
    Yields all JSON data.
    """
    for root, name in walk(top):
        if name.endswith('.json'):
            path = os.path.join(root, name)
            with open(path) as f:
                text = f.read()
                if text:
                    # Handle unreleased tag in $ref.
                    match = re.search(r'\d+__\d+__\d+', text)
                    if match:
                        tag = match.group(0)
                        if tag not in ocds_tags:
                            if ocds_version or not use_development_version:
                                text = text.replace(tag, ocds_tag)
                            else:
                                text = text.replace(ocds_schema_base_url + tag, development_base_url)
                    try:
                        yield (path, text, json.loads(text, object_pairs_hook=object_pairs_hook))
                    except json.decoder.JSONDecodeError as e:
                        # TODO assert False, '{} is not valid JSON ({})'.format(path, e)
                        pass


def walk_csv_data(top=cwd):
    """
    Yields all CSV data.
    """
    for root, name in walk(top):
        if name.endswith('.csv'):
            path = os.path.join(root, name)
            with open(path, newline='') as f:
                yield (path, csv.DictReader(f))
