"""Backend selection and orchestration."""

import threading
from typing import Callable, Dict, List, Optional, Protocol

from ..config import Settings, get_settings
from ..errors import EmptyWordError, SplitFailedError, UnknownMethodError


class Backend(Protocol):
    def split(self, word: str) -> List[str]: ...


def _make_charsplit(settings: Settings) -> Backend:
    from ..backends.charsplit_backend import CharsplitBackend

    return CharsplitBackend()


def _make_gcs(settings: Settings) -> Backend:
    from ..backends.gcs_backend import GcsBackend

    return GcsBackend(settings.dictionary_path, settings.transliteration_locales)


class SplitterService:
    """Routes split requests to lazily created, cached backends."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        factories: Optional[Dict[str, Callable[[Settings], Backend]]] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._factories = factories or {
            "charsplit": _make_charsplit,
            "german_compound_splitter": _make_gcs,
        }
        self._backends: Dict[str, Backend] = {}
        self._lock = threading.Lock()

    def _get_backend(self, method: str) -> Backend:
        backend = self._backends.get(method)
        if backend is None:
            with self._lock:
                backend = self._backends.get(method)
                if backend is None:
                    backend = self._factories[method](self._settings)
                    self._backends[method] = backend
        return backend

    def split(self, word: str, method: str = "charsplit") -> List[str]:
        word = word.strip()
        method = method.strip()
        if not word:
            raise EmptyWordError("Word cannot be empty")
        if method not in self._factories:
            raise UnknownMethodError(f"Unknown method {method}.")
        try:
            return self._get_backend(method).split(word)
        except Exception as exc:
            raise SplitFailedError(f"Unable to split {word} using {method}.") from exc


_service: Optional[SplitterService] = None
_service_lock = threading.Lock()


def get_service() -> SplitterService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = SplitterService()
    return _service
