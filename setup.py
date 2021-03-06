from setuptools import find_packages, setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='jscc',
    version='0.0.5',
    author='Open Contracting Partnership and Open Data Services Co-operative Limited',
    author_email='data@open-contracting.org',
    url='https://github.com/open-contracting/jscc',
    description='Tools for data standards that use JSON Schema and CSV codelists',
    license='BSD',
    packages=find_packages(exclude=['tests', 'tests.*']),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    install_requires=[
        'json-merge-patch',
        'jsonref',
        'jsonschema',
        'requests',
        'rfc3987',
        'strict-rfc3339',
    ],
    extras_require={
        'test': [
            'coveralls',
            'pytest',
            'pytest-cov',
            'pytest-vcr',
        ],
        'docs': [
            'Sphinx',
            'sphinx-autobuild',
            'sphinx-rtd-theme',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
