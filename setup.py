from setuptools import find_packages, setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='jscc',
    version='0.0.2',
    author='Open Contracting Partnership and Open Data Services Co-operative Limited',
    author_email='data@open-contracting.org',
    url='https://github.com/open-contracting/jscc',
    description='Tools for data standards that use JSON Schema and CSV codelists',
    license='BSD',
    packages=find_packages(exclude=['tests', 'tests.*']),
    long_description=long_description,
    install_requires=[
        'json-merge-patch',
        'jsonref',
        'jsonschema',
        'pytest',
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
            'sphinx_rtd_theme',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
    ],
)
