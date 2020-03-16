Changelog
=========

0.0.2 (Unreleased)
------------------

Added
~~~~~

-  :meth:`jscc.schema.extend_schema`

Changed
~~~~~~~

-  ``jscc.testing.schema`` is moved to :module:`jscc.schema`
-  ``jscc.schema.is_property_missing`` is renamed to :meth:`jscc.schema.is_missing_property`
-  :meth:`jscc.schema.is_codelist` accepts a list of field names, instead of a CSV reader
-  :meth:`jscc.filesystem.walk_csv_data` returns text content, fieldnames, and rows, instead of a CSV reader

0.0.1 (2020-03-13)
------------------

First release.
