"""Integration tests for /api/v1/providers endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── GET /api/v1/providers ─────────────────────────────────────────────────────

def test_list_providers_returns_200():
    resp = client.get("/api/v1/providers")
    assert resp.status_code == 200


def test_list_providers_has_all_slugs():
    resp = client.get("/api/v1/providers")
    data = resp.json()
    slugs = {p["provider"] for p in data["providers"]}
    assert {"openai", "anthropic", "huggingface", "mock"} == slugs


def test_list_providers_has_availability_field():
    resp = client.get("/api/v1/providers")
    for p in resp.json()["providers"]:
        assert "available" in p
        assert isinstance(p["available"], bool)


def test_mock_provider_always_available():
    resp = client.get("/api/v1/providers")
    mock_entry = next(p for p in resp.json()["providers"] if p["provider"] == "mock")
    assert mock_entry["available"] is True


# ── POST /api/v1/providers/evaluate ──────────────────────────────────────────

def test_evaluate_with_mock_provider_returns_200():
    resp = client.post("/api/v1/providers/evaluate", json={
        "text": "The model output is coherent and relevant.",
        "provider": "mock",
        "criteria": ["coherence", "fluency"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "mock"
    assert "coherence" in data["scores"]
    assert "fluency" in data["scores"]
    assert 0.0 <= data["overall"] <= 1.0
    assert isinstance(data["reasoning"], str)
    assert data["latency_ms"] >= 0


def test_evaluate_with_unconfigured_openai_returns_503(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.openai_api_key", None)
    resp = client.post("/api/v1/providers/evaluate", json={
        "text": "Hello world.",
        "provider": "openai",
    })
    assert resp.status_code == 503
    assert resp.json()["error"] == "provider_not_available"


def test_evaluate_unknown_provider_returns_400():
    resp = client.post("/api/v1/providers/evaluate", json={
        "text": "Hello world.",
        "provider": "nonexistent",  # type: ignore[arg-type]  # intentional bad value
    })
    # Pydantic rejects the Literal field → 422
    assert resp.status_code == 422


def test_evaluate_blank_text_returns_422():
    resp = client.post("/api/v1/providers/evaluate", json={
        "text": "   ",
        "provider": "mock",
    })
    assert resp.status_code == 422


def test_evaluate_response_has_error_envelope_on_failure(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.openai_api_key", None)
    resp = client.post("/api/v1/providers/evaluate", json={
        "text": "Some text.",
        "provider": "openai",
    })
    data = resp.json()
    assert "error" in data
    assert "message" in data


def test_evaluate_with_context():
    resp = client.post("/api/v1/providers/evaluate", json={
        "text": "Paris is the capital of France.",
        "context": "What is the capital of France?",
        "provider": "mock",
        "criteria": ["relevance"],
    })
    assert resp.status_code == 200
    assert "relevance" in resp.json()["scores"]
