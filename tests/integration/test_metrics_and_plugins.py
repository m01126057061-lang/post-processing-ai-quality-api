"""Integration tests for GET /metrics (Prometheus)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_200():
    resp = client.get("/metrics")
    assert resp.status_code == 200


def test_metrics_content_type_is_text():
    resp = client.get("/metrics")
    assert "text/plain" in resp.headers.get("content-type", "")


def test_metrics_contains_http_requests_total():
    # After at least one request, the counter should appear
    client.get("/health")
    resp = client.get("/metrics")
    assert "http_requests_total" in resp.text or "http_request" in resp.text


def test_plugin_registry_has_builtin_metrics():
    from app.scorers.registry import available_metrics
    metrics = available_metrics()
    assert set(metrics) >= {"coherence", "relevance", "fluency", "toxicity", "hallucination"}


def test_plugin_reload_is_idempotent():
    """Calling reload_plugins() twice should not duplicate built-in metrics."""
    from app.scorers.registry import available_metrics, reload_plugins
    reload_plugins()
    reload_plugins()
    metrics = available_metrics()
    assert len(metrics) == len(set(metrics)), "Duplicate metric names after reload"
