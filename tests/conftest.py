import pytest


@pytest.fixture(scope='module')
def vcr_config():
    # Avoid ImportWarning from YAML on PyPy 3.7. https://github.com/yaml/pyyaml/issues/534
    return {'serializer': 'json'}
