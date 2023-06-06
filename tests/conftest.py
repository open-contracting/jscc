import pytest


@pytest.fixture(scope='module')
def vcr_config():
    return {'serializer': 'json'}
