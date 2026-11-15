# tests/test_api.py  (web backend smoke tests)
import os

import pytest

pytestmark = pytest.mark.skipif(not os.path.exists("data/dictionary.json"),
                                reason="dictionary.json not built yet")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from src.api import app
    return TestClient(app)


def test_health(client):
    body = client.get("/api/health").json()
    assert body["entries"] > 1000


def test_check_returns_top3(client):
    body = client.post("/api/check", json={"text": "ڪتاپ"}).json()
    token = body["tokens"][0]
    assert token["known"] is False
    assert 1 <= len(token["suggestions"]) <= 3
    assert body["stats"]["unknown"] == 1


def test_lookup_both_directions(client):
    sd = client.get("/api/lookup", params={"q": "ڪتاب"}).json()
    assert sd["entry"]["key"] == "ڪتاب"
    en = client.get("/api/lookup", params={"q": "book"}).json()
    assert en["mode"] == "english" and en["results"]


def test_translate_falls_back_without_model(client):
    body = client.post("/api/translate", json={"text": "ڪتاب", "source": "sd", "target": "en"}).json()
    assert body["translation"]
    assert body["engine"] in ("nllb", "dictionary")


def test_index_page(client):
    assert "Sindhi" in client.get("/").text
