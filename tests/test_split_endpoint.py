import pytest


def test_split_charsplit(client):
    r = client.post("/split", json={"word": " Haustür "})
    assert r.status_code == 200
    body = r.json()
    assert body["word"] == "Haustür"
    assert body["splittable"] is True
    assert isinstance(body["components"], list)


def test_empty_word(client):
    assert client.post("/split", json={"word": "  "}).status_code == 400


def test_unknown_method(client):
    r = client.post("/split", json={"word": "Haustür", "method": "nope"})
    assert r.status_code == 400
    assert "nope" in r.json()["detail"]


def test_real_charsplit_contract():
    import pytest

    pytest.importorskip("compound_split")

    from fastapi.testclient import TestClient

    from german_word_splitter.main import app

    r = TestClient(app).post("/split", json={"word": "Haustür", "method": "charsplit"})
    assert r.status_code == 200
    assert set(r.json()) == {"word", "splittable", "components"}


@pytest.fixture
def real_gcs_client(tmp_path):
    pytest.importorskip("german_compound_splitter")

    from fastapi.testclient import TestClient

    from german_word_splitter.api.routes import get_service
    from german_word_splitter.config import Settings
    from german_word_splitter.main import create_app
    from german_word_splitter.services.splitter_service import SplitterService

    dictionary = tmp_path / "test.dic"
    dictionary.write_text("Haus\nTür\n", encoding="utf-8")
    service = SplitterService(
        settings=Settings(
            dictionary_path=str(dictionary),
            transliteration_locales=("de_DE.UTF-8",),
        )
    )
    app = create_app()
    app.dependency_overrides[get_service] = lambda: service
    return TestClient(app)


def test_real_german_compound_splitter_contract(real_gcs_client):
    r = real_gcs_client.post(
        "/split", json={"word": "Haustür", "method": "german_compound_splitter"}
    )
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"word", "splittable", "components"}
    assert body["word"] == "Haustür"
    assert isinstance(body["components"], list)


def test_real_german_compound_splitter_preserves_transliterated_input(real_gcs_client):
    r = real_gcs_client.post(
        "/split", json={"word": "Haustuer", "method": "german_compound_splitter"}
    )
    assert r.status_code == 200
    assert r.json()["components"] == ["Haus", "Tuer"]


def test_transliterate_option(client):
    r = client.post("/split", json={"word": "Haustür", "method": "charsplit", "transliterate": "C.UTF-8"})
    assert r.status_code == 200
    assert r.json()["components"] == ["Haus", "Tur"]


def test_transliterate_unconfigured_locale_is_rejected(client):
    r = client.post(
        "/split",
        json={"word": "Haustür", "method": "german_compound_splitter", "transliterate": "C.UTF-8"},
    )
    assert r.status_code == 400
    assert "TRANSLITERATION_LOCALES" in r.json()["detail"]


def test_split_failure_is_logged_and_rejected(client, service):
    service._factories["charsplit"] = lambda s: (_ for _ in ()).throw(RuntimeError("boom"))
    r = client.post("/split", json={"word": "Haustür", "method": "charsplit"})
    assert r.status_code == 400


def test_gcs_alias_and_default(client):
    assert client.post("/split", json={"word": "Haustür", "method": "gcs"}).status_code == 200
    assert client.post("/split", json={"word": "Haustür"}).status_code == 200


def test_info(client, monkeypatch):
    monkeypatch.setenv("GERMAN_WORD_SPLITTER_TRANSLITERATION_LOCALES", "de_DE en_US")
    for path in ("/info", "/config"):
        body = client.get(path).json()
        assert body["default_method"] == "gcs"
        assert body["transliteration_locales"] == ["de_DE", "en_US"]
        assert body["version"]
