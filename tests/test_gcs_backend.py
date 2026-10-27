import pytest

pytest.importorskip("german_compound_splitter")

from german_word_splitter.backends.gcs_backend import GcsBackend  # noqa: E402

WORDS = [
    "Einkäufe",
    "Donau",
    "Dampf",
    "Schiff",
    "Fahrt",
    "Kapitän",
    "Mütze",
    "Abzeichen",
    "Straßen",
]

EINKAUFE = ["Einkäufe"]
DONAU = ["Donau", "Dampf", "Schiff", "Fahrt", "Kapitän", "Mütze", "Abzeichen"]
STRASSEN = ["Straßen", "Fahrt"]

DONAU_ORIGINAL = "Donaudampfschifffahrtskapitänsmützenabzeichen"
DONAU_DE = "Donaudampfschifffahrtskapitaensmuetzenabzeichen"
DONAU_EN = "Donaudampfschifffahrtskapitansmutzenabzeichen"


@pytest.fixture
def dictionary(tmp_path):
    path = tmp_path / "test.dic"
    path.write_text("\n".join(WORDS) + "\n", encoding="utf-8")
    return str(path)


@pytest.mark.parametrize(
    "word, expected",
    [
        ("Einkäufe", EINKAUFE),
        (DONAU_ORIGINAL, DONAU),
        ("Straßenfahrt", STRASSEN),
    ],
)
@pytest.mark.parametrize(
    "locales", [(), ("de_DE.UTF-8",), ("en_US.UTF-8",), ("de_DE.UTF-8", "en_US.UTF-8")]
)
def test_original_spelling_with_any_locales(dictionary, locales, word, expected):
    assert GcsBackend(dictionary, locales).split(word) == expected


@pytest.mark.parametrize(
    "locales", [("de_DE.UTF-8",), ("de_DE.UTF-8", "en_US.UTF-8"), ("en_US.UTF-8", "de_DE.UTF-8")]
)
@pytest.mark.parametrize(
    "word, expected",
    [
        ("Einkaeufe", EINKAUFE),
        (DONAU_DE, DONAU),
        ("Strassenfahrt", STRASSEN),
    ],
)
def test_german_transliteration(dictionary, locales, word, expected):
    assert GcsBackend(dictionary, locales).split(word) == expected


@pytest.mark.parametrize(
    "locales", [("en_US.UTF-8",), ("de_DE.UTF-8", "en_US.UTF-8")]
)
@pytest.mark.parametrize(
    "word, expected",
    [
        ("Einkaufe", EINKAUFE),
        (DONAU_EN, DONAU),
        ("Strassenfahrt", STRASSEN),
    ],
)
def test_english_transliteration(dictionary, locales, word, expected):
    assert GcsBackend(dictionary, locales).split(word) == expected


@pytest.mark.parametrize(
    "word, expected",
    [
        ("Einkaeufe", ["Einkaeufe"]),
        ("Einkaufe", ["Einkaufe"]),
        (DONAU_DE, DONAU[:4]),
        (DONAU_EN, DONAU[:4]),
    ],
)
def test_transliteration_is_off_by_default(dictionary, word, expected):
    assert GcsBackend(dictionary).split(word) == expected


def test_locale_specific_forms_are_not_mixed(dictionary):
    assert GcsBackend(dictionary, ("de_DE.UTF-8",)).split("Einkaufe") == ["Einkaufe"]
    assert GcsBackend(dictionary, ("en_US.UTF-8",)).split("Einkaeufe") == ["Einkaeufe"]
