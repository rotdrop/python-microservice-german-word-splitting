import sys
from types import SimpleNamespace

import pytest

from german_word_splitter.backends.gcs_backend import GcsBackend


def create_backend(monkeypatch, dissect):
    comp_split = SimpleNamespace(
        read_dictionary_from_file=lambda _: [],
        dissect=dissect,
        merge_fractions=lambda dissection: dissection,
    )
    monkeypatch.setitem(
        sys.modules,
        "german_compound_splitter",
        SimpleNamespace(comp_split=comp_split),
    )
    return GcsBackend("dictionary.dic")


def test_gcs_backend_treats_empty_dissection_as_unsplittable(monkeypatch):
    def dissect(word, dictionary, make_singular):
        raise IndexError("list index out of range")

    backend = create_backend(monkeypatch, dissect)

    assert backend.split("einkaeufe") == ["einkaeufe"]


def test_gcs_backend_preserves_other_failures(monkeypatch):
    def dissect(word, dictionary, make_singular):
        raise RuntimeError("unexpected failure")

    backend = create_backend(monkeypatch, dissect)

    with pytest.raises(RuntimeError, match="unexpected failure"):
        backend.split("Haustür")
