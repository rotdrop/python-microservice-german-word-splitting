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


def _fake_transliterate(text, locale):
    return text.replace("ä", "ae" if locale.startswith("de") else "a")


def _umlaut_service(monkeypatch, locales=()):
    from german_word_splitter.config import Settings
    from german_word_splitter.services import splitter_service

    monkeypatch.setattr(splitter_service, "transliterate", _fake_transliterate)
    backend = type("B", (), {"split": lambda self, w: ["Käse", "Brot"]})()
    return SplitterService(
        settings=Settings(transliteration_locales=locales),
        factories={"charsplit": lambda s: backend, "gcs": lambda s: backend},
    )


def test_transliterate_charsplit_skips_check(monkeypatch):
    svc = _umlaut_service(monkeypatch)
    assert svc.split("x", "charsplit", "de_DE") == ["Kaese", "Brot"]


def test_transliterate_unconfigured_locale_fails(monkeypatch):
    from german_word_splitter.errors import TransliterationError

    with pytest.raises(TransliterationError):
        _umlaut_service(monkeypatch, ("de_DE",)).split("x", "gcs", "en_US")


def test_transliterate_configured_or_unmodified(monkeypatch):
    svc = _umlaut_service(monkeypatch, ("de_AT",))
    assert svc.split("x", "gcs", "de_DE") == ["Kaese", "Brot"]
    svc = _umlaut_service(monkeypatch, ("en_US",))
    assert svc.split("x", "gcs", "en_GB") == ["Kase", "Brot"]


def test_iconv_transliteration():
    from german_word_splitter.transliteration import transliterate

    assert transliterate("Käse Straße", "C.UTF-8") == "Kase Strasse"


def test_iconv_failure_is_reported(monkeypatch):
    import subprocess

    from german_word_splitter import transliteration
    from german_word_splitter.errors import TransliterationError

    def boom(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "iconv")

    monkeypatch.setattr(transliteration.subprocess, "run", boom)
    with pytest.raises(TransliterationError):
        transliteration.transliterate("Käse", "C.UTF-8")


def test_unavailable_locale_is_reported():
    from german_word_splitter.errors import TransliterationError
    from german_word_splitter.transliteration import transliterate

    with pytest.raises(TransliterationError):
        transliterate("Käse", "xx_YY.UTF-8")


def test_get_service_is_cached(monkeypatch):
    from german_word_splitter.services import splitter_service

    monkeypatch.setattr(splitter_service, "_service", None)
    assert splitter_service.get_service() is splitter_service.get_service()
