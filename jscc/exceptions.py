class JSCCError(Exception):
    """Base class for exceptions from within this package"""


class DuplicateKeyError(JSCCError):
    """Raised if a JSON message has members with duplicate names"""


class JSCCWarning(UserWarning):
    """Base class for warnings from within this package"""


class CodelistEnumWarning(JSCCWarning):
    pass


class DeepPropertiesWarning(JSCCWarning):
    pass


class ItemsTypeWarning(JSCCWarning):
    pass


class LetterCaseWarning(JSCCWarning):
    pass


class MergePropertiesWarning(JSCCWarning):
    pass


class MetadataPresenceWarning(JSCCWarning):
    pass


class NullTypeWarning(JSCCWarning):
    pass


class ObjectIdWarning(JSCCWarning):
    pass


class RefWarning(JSCCWarning):
    pass


class SchemaCodelistsMatchWarning(JSCCWarning):
    pass


class SchemaWarning(JSCCWarning):
    pass
