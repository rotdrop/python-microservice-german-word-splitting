"""Backend wrapping german_compound_splitter."""

from typing import List, Sequence


class GcsBackend:
    def __init__(
        self, dictionary_path: str, transliteration_locales: Sequence[str] = ()
    ) -> None:
        from german_compound_splitter import comp_split

        self._comp_split = comp_split
        self._ahocs = comp_split.read_dictionary_from_file(
            dictionary_path,
            transliteration_locales=list(transliteration_locales) or None,
        )

    def split(self, word: str) -> List[str]:
        dissection = self._comp_split.dissect(word, self._ahocs, make_singular=False)
        return self._comp_split.merge_fractions(dissection)
