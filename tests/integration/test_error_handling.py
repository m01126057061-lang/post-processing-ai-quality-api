"""Integration tests for structured error handling."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.request import MAX_BATCH_SIZE, MAX_TEXT_LENGTH

client = TestClient(app)


# ── Validation errors (422) ────────────────────────────────────────────────

def test_evaluate_blank_text_returns_422():
    resp = client.post("/api/v1/evaluate", json={"text": "   ", "metrics": ["fluency"]})
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"] == "validation_error"
    assert any("blank" in d["message"] for d in data["details"])


def test_evaluate_unknown_metric_returns_422():
    resp = client.post("/api/v1/evaluate", json={"text": "hello", "metrics": ["fake"]})
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"] == "validation_error"
    assert any("Unknown metric" in d["message"] for d in data["details"])


def test_filter_batch_too_large_returns_422():
    resp = client.post("/api/v1/filter", json={
        "texts": ["x"] * (MAX_BATCH_SIZE + 1),
        "metrics": ["fluency"],
    })
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"] == "validation_error"


def test_pipeline_filter_before_score_returns_422():
    resp = client.post("/api/v1/pipeline/run", json={
        "texts": ["hello"],
        "steps": [{"type": "filter", "threshold": 0.5}],
    })
    assert resp.status_code == 422
    assert "filter" in resp.json()["message"].lower()


# ── Error response structure ───────────────────────────────────────────────

def test_error_response_has_required_fields():
    resp = client.post("/api/v1/evaluate", json={"text": "", "metrics": ["fluency"]})
    data = resp.json()
    assert "error" in data
    assert "message" in data
    assert "details" in data


def test_x_request_id_echoed_in_response():
    resp = client.post(
        "/api/v1/evaluate",
        json={"text": "   "},
        headers={"X-Request-ID": "test-id-123"},
    )
    assert resp.headers.get("x-request-id") == "test-id-123"


# ── Health endpoints ───────────────────────────────────────────────────────

def test_health_liveness():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_readiness_returns_checks():
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "checks" in data


# ── 404 for unknown route ──────────────────────────────────────────────────

def test_unknown_route_returns_404():
    resp = client.get("/api/v1/nonexistent")
    assert resp.status_code == 404
