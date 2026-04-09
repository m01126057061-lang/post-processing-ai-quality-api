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
    resp = client.post("/api/v1/evaluate", json={"text": "Valid.", "metrics": ["toxicity"]})
    assert resp.status_code in (400, 422)


def test_evaluate_request_id_header():
    resp = client.post("/api/v1/evaluate", json={"text": "Test."})
    assert "x-request-id" in {k.lower() for k in resp.headers}
