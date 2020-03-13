import json

import pytest

from jscc.exceptions import DuplicateKeyError
from jscc.testing.util import rejecting_dict


def test_rejecting_dict():
    with pytest.raises(DuplicateKeyError) as excinfo:
        json.loads('{"x": 0, "x": 1}', object_pairs_hook=rejecting_dict)

    assert str(excinfo.value) == 'x'
