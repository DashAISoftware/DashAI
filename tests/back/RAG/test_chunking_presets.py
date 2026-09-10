"""Tests for the chunking-presets endpoint."""

from fastapi.testclient import TestClient


def test_chunking_presets_returns_four_presets(client: TestClient):
    response = client.get("/api/v1/rag/chunking-presets")
    assert response.status_code == 200
    data = response.json()
    assert [p["key"] for p in data] == ["small", "paragraph", "page", "large"]


def test_every_preset_is_a_complete_recipe(client: TestClient):
    data = client.get("/api/v1/rag/chunking-presets").json()
    for preset in data:
        assert preset["component"] == "CharacterChunkModel"
        assert isinstance(preset["params"]["chunk_size"], int)
        assert isinstance(preset["params"]["chunk_overlap"], int)


def test_paragraph_preset_matches_the_session_default(client: TestClient):
    data = client.get("/api/v1/rag/chunking-presets").json()
    paragraph = next(p for p in data if p["key"] == "paragraph")
    assert paragraph["params"]["chunk_size"] == 500
    assert paragraph["params"]["chunk_overlap"] == 50

    defaults = client.get("/api/v1/rag/session-defaults").json()
    assert defaults["chunking_model"]["component"] == paragraph["component"]
    assert defaults["chunking_model"]["params"] == paragraph["params"]


def test_presets_are_localized(client: TestClient):
    english = client.get("/api/v1/rag/chunking-presets").json()
    spanish = client.get(
        "/api/v1/rag/chunking-presets", headers={"Accept-Language": "es"}
    ).json()

    by_key_en = {p["key"]: p for p in english}
    by_key_es = {p["key"]: p for p in spanish}

    assert by_key_en["paragraph"]["display_name"] == "Paragraph length"
    assert by_key_es["paragraph"]["display_name"] == "Largo de un párrafo"
    # Names arrive as plain strings, never as language objects.
    assert isinstance(by_key_es["small"]["display_name"], str)
    assert "caracteres" in by_key_es["small"]["description"]


def test_retriever_presets_are_localized(client: TestClient):
    spanish = client.get(
        "/api/v1/rag/retriever-presets",
        params={"top_k": 10},
        headers={"Accept-Language": "es"},
    ).json()
    by_key = {p["key"]: p for p in spanish}
    assert by_key["hybrid"]["display_name"] == "Híbrido"
    assert by_key["keyword"]["display_name"] == "Palabras clave"


def test_session_defaults_need_no_download(client: TestClient):
    """The defaults must never gate session creation behind a model download.

    Keyword retrieval is chosen precisely because it pulls no weights; if this
    ever changes, creating a session with defaults starts failing with 409.
    """
    defaults = client.get("/api/v1/rag/session-defaults").json()
    assert defaults["retriever_model"]["component"] == "BM25Retriever"

    required = client.post(
        "/api/v1/component/downloads/required",
        json={"model_name": None, "parameters": defaults},
    )
    assert required.status_code == 200
    assert required.json() == []


def test_session_defaults_carry_display_names(client: TestClient):
    defaults = client.get(
        "/api/v1/rag/session-defaults", headers={"Accept-Language": "es"}
    ).json()
    for key in ("chunking_model", "retriever_model", "prompt"):
        display_name = defaults[key]["display_name"]
        assert isinstance(display_name, str)
        assert display_name
        assert display_name != defaults[key]["component"], (
            f"{key} still falls back to its class name"
        )


def test_session_defaults_follow_the_request_language(client: TestClient):
    spanish = client.get(
        "/api/v1/rag/session-defaults", headers={"Accept-Language": "es"}
    ).json()
    assert spanish["prompt"]["params"]["language"] == "es"

    # A language the default prompt has no template for falls back to English.
    german = client.get(
        "/api/v1/rag/session-defaults", headers={"Accept-Language": "de"}
    ).json()
    assert german["prompt"]["params"]["language"] == "en"
