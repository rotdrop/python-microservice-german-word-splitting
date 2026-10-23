"""Backend wrapping the compound-split package (char_split)."""

from typing import List


class CharsplitBackend:
    def __init__(self) -> None:
        from compound_split import char_split

        self._splitter = char_split

    def split(self, word: str) -> List[str]:
        results = self._splitter.split_compound(word)
        return [results[0][1], results[0][2]]
