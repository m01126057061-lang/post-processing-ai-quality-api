"""
Integration tests for POST /api/v1/evaluate.

These tests use FastAPI TestClient with real scorer instances.
ML-backed scorers (coherence, relevance) will lazy-load on first call.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_evaluate_fluency_only():
    resp = client.post("/api/v1/evaluate", json={
        "text": "The assistant provided a clear and concise answer.",
        "metrics": ["fluency"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "fluency" in data["scores"]["breakdown"]
    assert 0.0 <= data["scores"]["overall"] <= 1.0


def test_evaluate_unknown_metric_returns_400():
    resp = client.post("/api/v1/evaluate", json={
        "text": "Hello world.",
        "metrics": ["nonexistent_metric"],
    })
    assert resp.status_code == 400


def test_evaluate_all_metrics_with_context():
    resp = client.post("/api/v1/evaluate", json={
        "text": "Paris is the capital of France and a major European city.",
        "context": "What is the capital of France?",
        "metrics": ["coherence", "relevance", "fluency"],
    })
    assert resp.status_code == 200
    data = resp.json()
    breakdown = data["scores"]["breakdown"]
    assert set(breakdown.keys()) == {"coherence", "relevance", "fluency"}
    assert all(0.0 <= v <= 1.0 for v in breakdown.values())
    assert isinstance(data["passed"], bool)


def test_evaluate_relevance_without_context_returns_neutral():
    resp = client.post("/api/v1/evaluate", json={
        "text": "The sky is blue.",
        "metrics": ["relevance"],
    })
    assert resp.status_code == 200
    # No context provided → relevance returns 0.5 (neutral)
    assert resp.json()["scores"]["breakdown"]["relevance"] == 0.5
