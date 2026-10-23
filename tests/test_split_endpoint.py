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

    r = TestClient(app).post("/split", json={"word": "Haustür"})
    assert r.status_code == 200
    assert set(r.json()) == {"word", "splittable", "components"}
