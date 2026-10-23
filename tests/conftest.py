from typing import List

import pytest
from fastapi.testclient import TestClient

from german_word_splitter.api.routes import get_service
from german_word_splitter.main import create_app
from german_word_splitter.services.splitter_service import SplitterService


class FakeBackend:
    def __init__(self, parts: List[str]) -> None:
        self.parts = parts

    def split(self, word: str) -> List[str]:
        return self.parts


@pytest.fixture
def service() -> SplitterService:
    return SplitterService(
        factories={
            "charsplit": lambda s: FakeBackend(["Haus", "Tür"]),
            "german_compound_splitter": lambda s: FakeBackend(["Haus", "Tür"]),
        }
    )


@pytest.fixture
def client(service: SplitterService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_service] = lambda: service
    return TestClient(app)
