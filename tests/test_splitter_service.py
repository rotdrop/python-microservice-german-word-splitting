import pytest

from german_word_splitter.errors import (
    EmptyWordError,
    SplitFailedError,
    UnknownMethodError,
)
from german_word_splitter.services.splitter_service import SplitterService


def test_routes_by_method():
    calls = []

    class B:
        def __init__(self, name):
            self.name = name

        def split(self, word):
            calls.append(self.name)
            return [word]

    svc = SplitterService(factories={"a": lambda s: B("a"), "b": lambda s: B("b")})
    svc.split("x", "a")
    svc.split("x", "b")
    assert calls == ["a", "b"]


def test_backend_cached():
    created = []

    def factory(settings):
        created.append(1)
        return type("B", (), {"split": lambda self, w: [w]})()

    svc = SplitterService(factories={"a": factory})
    svc.split("x", "a")
    svc.split("y", "a")
    assert len(created) == 1


def test_errors(service):
    with pytest.raises(EmptyWordError):
        service.split(" ")
    with pytest.raises(UnknownMethodError):
        service.split("x", "bad")


def test_backend_failure_wrapped():
    def factory(settings):
        raise RuntimeError("boom")

    with pytest.raises(SplitFailedError):
        SplitterService(factories={"a": factory}).split("x", "a")
