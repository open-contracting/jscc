from setuptools import find_packages, setup

setup(
    name='jscc',
    version='0.0.0',
    packages=find_packages(),
    install_requires=[
        'jsonref',
        'jsonschema',
        'pytest>=3.6',
        'rfc3987',
        'strict-rfc3339',
    ],
)
