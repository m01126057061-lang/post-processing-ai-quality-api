"""Integration tests for health endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_liveness_200():
    assert client.get("/health").status_code == 200


def test_health_liveness_shape():
    assert "status" in client.get("/health").json()


def test_health_liveness_status_value():
    assert client.get("/health").json()["status"] in ("ok", "healthy", "up")


def test_health_readiness_200():
    assert client.get("/health/ready").status_code == 200


def test_health_readiness_shape():
    assert "status" in client.get("/health/ready").json()


def test_health_no_auth_required():
    resp = client.get("/health")
    assert resp.status_code not in (401, 403)
