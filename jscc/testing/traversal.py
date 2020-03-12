import csv
import json
import os
import re

import requests

from jscc.testing.util import rejecting_dict

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


def walk_json_data(**kwargs):
    """
    Walks a directory tree, and yields tuples consisting of a file path, text content, and JSON data.
    """
    for root, name in walk(**kwargs):
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
                        yield path, text, json.loads(text, object_pairs_hook=rejecting_dict)
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
