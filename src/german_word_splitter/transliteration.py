"""Locale dependent transliteration through iconv."""

import locale as _locale
import re
import subprocess
from typing import Sequence

from .errors import LocaleNotInstalledError, TransliterationError


def language(locale: str) -> str:
    """Language part of a locale name like de_DE, de-AT or en_US.UTF-8."""
    return re.split(r"[_\-.@]", locale.strip().lower())[0]


def is_configured(locale: str, configured: Sequence[str]) -> bool:
    """Whether the locale is covered by the configured ones (language part only)."""
    return any(language(locale) == language(c) for c in configured)


def _locale_name(locale: str) -> str:
    name, dot, codeset = locale.strip().partition(".")
    return f"{name.replace('-', '_')}.{codeset}" if dot else f"{name.replace('-', '_')}.UTF-8"


def transliterate(text: str, locale: str) -> str:
    """Transliterate text with ``iconv -t ASCII//TRANSLIT`` under the given locale.

    The locale has to be installed on the system, otherwise iconv falls back to
    the C locale or emits ``?``; the latter is reported as an error.
    """
    try:
        proc = subprocess.run(
            ["iconv", "-f", "UTF-8", "-t", "ASCII//TRANSLIT"],
            input=text.encode("utf-8"),
            capture_output=True,
            env={"LC_ALL": _locale_name(locale), "PATH": "/usr/bin:/bin"},
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise TransliterationError(
            f"Unable to transliterate {text} for locale {locale}."
        ) from exc
    result = proc.stdout.decode("ascii", errors="replace")
    if result.count("?") > text.count("?"):
        raise TransliterationError(
            f"Locale {locale} is not available for transliteration of {text}."
        )
    return result


def check_locales_installed(locales: Sequence[str]) -> None:
    """Raise LocaleNotInstalledError unless all locales are installed on the system.

    Meant to be called at startup: setlocale() is process wide and not thread safe.
    """
    saved = _locale.setlocale(_locale.LC_CTYPE)
    missing = []
    try:
        for name in locales:
            try:
                _locale.setlocale(_locale.LC_CTYPE, _locale_name(name))
            except _locale.Error:
                missing.append(name)
    finally:
        _locale.setlocale(_locale.LC_CTYPE, saved)
    if missing:
        raise LocaleNotInstalledError(
            "Locales configured in GERMAN_WORD_SPLITTER_TRANSLITERATION_LOCALES "
            f"are not installed: {', '.join(missing)}"
        )
