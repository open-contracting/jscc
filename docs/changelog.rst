Changelog
=========

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
