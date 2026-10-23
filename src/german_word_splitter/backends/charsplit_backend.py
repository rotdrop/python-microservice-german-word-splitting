"""Backend wrapping CharSplit."""

from typing import List


class CharsplitBackend:
    def __init__(self) -> None:
        from charsplit import Splitter

        self._splitter = Splitter()

    def split(self, word: str) -> List[str]:
        results = self._splitter.split_compound(word)
        return [results[0][1], results[0][2]]
