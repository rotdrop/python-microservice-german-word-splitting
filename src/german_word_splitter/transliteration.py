"""Locale dependent transliteration of German umlauts and ß."""

import re
from typing import Dict

# German: ä -> ae, other locales (e.g. en_US, as iconv does): ä -> a.
# Mirrors the tables of german_compound_splitter.
_TABLES: Dict[str, Dict[str, str]] = {
    "de": {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"},
    "default": {"ä": "a", "ö": "o", "ü": "u", "ß": "ss"},
}


def _table_name(locale: str) -> str:
    language = re.split(r"[_\-.@]", locale.strip().lower())[0]
    return language if language in _TABLES else "default"


def same_transliteration(a: str, b: str) -> bool:
    """Whether both locales transliterate identically."""
    return _table_name(a) == _table_name(b)


def transliterate(text: str, locale: str) -> str:
    table = _TABLES[_table_name(locale)]
    out = []
    for char in text:
        repl = table.get(char.lower())
        if repl is None:
            out.append(char)
        elif char.isupper():
            out.append(repl.capitalize())
        else:
            out.append(repl)
    return "".join(out)
