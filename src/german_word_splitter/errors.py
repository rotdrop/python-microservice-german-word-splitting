"""Domain/service exceptions."""


class SplitterError(Exception):
    """Base class for splitting errors."""


class EmptyWordError(SplitterError):
    """The word to split is empty or blank."""


class UnknownMethodError(SplitterError):
    """The requested splitting method is not supported."""


class SplitFailedError(SplitterError):
    """A backend failed to split the word."""
