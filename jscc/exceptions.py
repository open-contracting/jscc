class JSCCError(Exception):
    """Base class for exceptions from within this package"""


class DuplicateKeyError(JSCCError):
    """Raised if a JSON message has members with duplicate names"""
