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


def _umlaut_service(locales=()):
    from german_word_splitter.config import Settings

    backend = type("B", (), {"split": lambda self, w: ["Käse", "Brot"]})()
    return SplitterService(
        settings=Settings(transliteration_locales=locales),
        factories={"charsplit": lambda s: backend, "gcs": lambda s: backend},
    )


def test_transliterate_charsplit_skips_check():
    assert _umlaut_service().split("x", "charsplit", "de_DE") == ["Kaese", "Brot"]


def test_transliterate_unconfigured_locale_fails():
    from german_word_splitter.errors import TransliterationError

    with pytest.raises(TransliterationError):
        _umlaut_service(("de_DE",)).split("x", "gcs", "en_US")


def test_transliterate_configured_or_unmodified():
    assert _umlaut_service(("de_AT",)).split("x", "gcs", "de_DE") == ["Kaese", "Brot"]
    assert _umlaut_service(("en_US",)).split("x", "gcs", "en_GB") == ["Kase", "Brot"]
