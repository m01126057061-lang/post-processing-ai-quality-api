"""Integration tests for POST /api/v1/evaluate."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_evaluate_200():
    assert client.post("/api/v1/evaluate", json={"text": "The sky is blue."}).status_code == 200


def test_evaluate_response_shape():
    data = client.post("/api/v1/evaluate", json={"text": "Hello world."}).json()
    assert "text" in data
    assert "scores" in data
    assert "overall" in data["scores"]
    assert "breakdown" in data["scores"]
    assert "passed" in data


def test_evaluate_single_metric():
    resp = client.post("/api/v1/evaluate", json={"text": "A sentence.", "metrics": ["coherence"]})
    assert resp.status_code == 200
    assert "coherence" in resp.json()["scores"]["breakdown"]


def test_evaluate_all_metrics():
    resp = client.post("/api/v1/evaluate", json={
        "text": "Test.", "metrics": ["coherence", "relevance", "fluency"]
    })
    assert set(resp.json()["scores"]["breakdown"].keys()) == {"coherence", "relevance", "fluency"}


def test_evaluate_with_context():
    resp = client.post("/api/v1/evaluate", json={
        "text": "Paris is the capital of France.",
        "context": "What is the capital of France?",
        "metrics": ["relevance"],
    })
    assert resp.status_code == 200
    assert "relevance" in resp.json()["scores"]["breakdown"]


def test_evaluate_overall_in_range():
    overall = client.post("/api/v1/evaluate", json={"text": "Some text."}).json()["scores"]["overall"]
    assert 0.0 <= overall <= 1.0


def test_evaluate_passed_is_bool():
    assert isinstance(client.post("/api/v1/evaluate", json={"text": "Some text."}).json()["passed"], bool)


def test_evaluate_blank_text_422():
    assert client.post("/api/v1/evaluate", json={"text": "   "}).status_code == 422


def test_evaluate_text_too_long_422():
    assert client.post("/api/v1/evaluate", json={"text": "x" * 10_001}).status_code == 422


def test_evaluate_empty_metrics_422():
    assert client.post("/api/v1/evaluate", json={"text": "Hello.", "metrics": []}).status_code == 422


def test_evaluate_unknown_metric_error():
    resp = client.post("/api/v1/evaluate", json={"text": "Valid.", "metrics": ["nonexistent_metric"]})
    assert resp.status_code in (400, 422)


def test_evaluate_request_id_header():
    resp = client.post("/api/v1/evaluate", json={"text": "Test."})
    assert "x-request-id" in {k.lower() for k in resp.headers}


# ── New fields (evaluation_id + explanations) ─────────────────────────────────

def test_evaluate_returns_evaluation_id():
    data = client.post("/api/v1/evaluate", json={"text": "A test sentence."}).json()
    # evaluation_id is a UUID string when audit is enabled, None when disabled
    assert "evaluation_id" in data
    if data["evaluation_id"] is not None:
        assert isinstance(data["evaluation_id"], str)
        assert len(data["evaluation_id"]) == 36  # UUID4


def test_evaluate_returns_explanations():
    data = client.post("/api/v1/evaluate", json={
        "text": "The report was clear and well-structured.",
        "metrics": ["coherence", "fluency"],
    }).json()
    assert "explanations" in data
    assert data["explanations"] is not None
    assert "coherence" in data["explanations"]
    assert "fluency" in data["explanations"]
    # Explanations are non-empty strings
    for key, val in data["explanations"].items():
        assert isinstance(val, str) and len(val) > 0


def test_evaluate_explanation_contains_band():
    """Explanation string should contain a band label."""
    data = client.post("/api/v1/evaluate", json={
        "text": "Short sentence.",
        "metrics": ["fluency"],
    }).json()
    explanation = data["explanations"]["fluency"]
    assert any(band in explanation for band in ("high", "good", "moderate", "low", "very low"))
