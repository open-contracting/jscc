Changelog
=========

0.1.1 (2023-04-19)
------------------

Changed
~~~~~~~

-  Drop support for Python 3.6 (end-of-life 2021-12-23).

Fixed
~~~~~

-  :meth:`jscc.testing.checks.get_empty_files` correctly returns JSON files that are whitespace only.

0.1.0 (2022-10-28)
------------------

Changed
~~~~~~~

-  Update to `jsonref <https://jsonref.readthedocs.io/>`__ 1.0's API.

0.0.9 (2022-04-26)
------------------

Changed
~~~~~~~

-  Changed dependency from `rfc3987 <https://pypi.org/project/rfc3987/>`__ (GPL) to `rfc3986-validator <https://pypi.org/project/rfc3986-validator/>`__ (MIT).

0.0.8 (2022-03-08)
------------------

Added
~~~~~

-  :meth:`jscc.testing.checks.validate_array_items` warns if a field whose ``type`` property includes "array" is missing the ``items`` property.

0.0.7 (2021-11-04)
------------------

Changed
~~~~~~~

-  ``jscc.testing.checks``: :meth:`~jscc.testing.checks.get_empty_files`, :meth:`~jscc.testing.checks.get_misindented_files`, :meth:`~jscc.testing.checks.get_invalid_json_files` and :meth:`~jscc.testing.checks.get_invalid_csv_files` accept keyword arguments to pass to :meth:`jscc.testing.filesystem.walk` and :meth:`jscc.testing.filesystem.walk_json_data`.

0.0.6 (2021-07-19)
------------------

Fixed
~~~~~

-  :meth:`jscc.testing.checks.validate_object_id` supports the ``omitWhenMerged`` property.

0.0.5 (2021-04-10)
------------------

Added
~~~~~

-  Add Python wheels distribution.

0.0.4 (2020-06-23)
------------------

Fixed
~~~~~

-  :meth:`jscc.testing.checks.validate_ref` supports integers in JSON Pointers.
-  :meth:`jscc.testing.checks.validate_metadata_presence` allows missing ``type`` property if configured via ``allow_missing`` argument.
-  :meth:`jscc.testing.filesystem.tracked` supports Windows.

0.0.3 (2020-03-17)
------------------

Added
~~~~~

-  :meth:`jscc.testing.checks.validate_merge_properties` warns if merge properties are set to ``false`` or ``null``.
-  Expand docstrings for ``jscc.schema.checks.validate_*`` methods.

Changed
~~~~~~~

-  :meth:`jscc.testing.checks.validate_merge_properties` no longer warns about nullable fields, and no longer accepts an ``allow_null`` argument.
-  :meth:`jscc.testing.checks.validate_null_type` warns if an array of objects is nullable. This check was previously performed by :meth:`jscc.testing.checks.validate_merge_properties`.
-  :meth:`jscc.testing.checks.validate_null_type`'s ``should_be_nullable`` argument is renamed to ``expect_null``.
-  Clarify warning messages.

0.0.2 (2020-03-16)
------------------

Added
~~~~~

-  :meth:`jscc.schema.extend_schema`
-  :meth:`jscc.testing.checks.get_invalid_csv_files`

Changed
~~~~~~~

-  :meth:`jscc.schema.is_codelist` accepts a list of field names, instead of a CSV reader.
-  :meth:`jscc.testing.filesystem.walk_csv_data` returns text content, fieldnames, and rows, instead of a CSV reader.
-  ``jscc.testing.schema`` is moved to :mod:`jscc.schema`.
-  ``jscc.schema.is_property_missing`` is renamed to :meth:`jscc.schema.is_missing_property`.

0.0.1 (2020-03-15)
------------------

First release.
