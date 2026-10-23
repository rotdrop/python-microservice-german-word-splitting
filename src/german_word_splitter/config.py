"""Environment-driven settings."""

import os
from dataclasses import dataclass

DICTIONARY_ENV = "GERMAN_WORD_SPLITTER_DICTIONARY"
DEFAULT_DICTIONARY = "german.dic"


@dataclass(frozen=True)
class Settings:
    dictionary_path: str = DEFAULT_DICTIONARY


def get_settings() -> Settings:
    return Settings(dictionary_path=os.environ.get(DICTIONARY_ENV, DEFAULT_DICTIONARY))
