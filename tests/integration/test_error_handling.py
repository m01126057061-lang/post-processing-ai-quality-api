"""Integration tests for error handling, middleware, and response envelopes."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_request_id_header_on_evaluate():
    resp = client.post("/api/v1/evaluate", json={"text": "Hello."})
    assert "x-request-id" in {k.lower() for k in resp.headers}


def test_request_id_non_empty():
    resp = client.post("/api/v1/evaluate", json={"text": "Hello."})
    headers = {k.lower(): v for k, v in resp.headers.items()}
    assert len(headers.get("x-request-id", "")) > 0


def test_request_id_on_filter():
    resp = client.post("/api/v1/filter", json={"texts": ["Hello."], "threshold": 0.5})
    assert "x-request-id" in {k.lower() for k in resp.headers}


def test_validation_error_blank_text():
    resp = client.post("/api/v1/evaluate", json={"text": "  "})
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data or "error" in data


def test_unknown_route_404():
    assert client.get("/api/v1/does-not-exist").status_code == 404


def test_method_not_allowed_on_evaluate():
    assert client.get("/api/v1/evaluate").status_code == 405


def test_filter_validation_error_envelope():
    resp = client.post("/api/v1/filter", json={"texts": [], "threshold": 0.5})
    assert resp.status_code == 422
    assert "detail" in resp.json() or "error" in resp.json()
