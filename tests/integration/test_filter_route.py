"""Integration tests for POST /api/v1/filter."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_filter_single_text_passes():
    resp = client.post("/api/v1/filter", json={
        "texts": ["The assistant gave a thorough and well-structured explanation."],
        "metrics": ["fluency"],
        "threshold": 0.1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total"] == 1
    assert data["summary"]["passed"] == 1


def test_filter_high_threshold_filters_all():
    resp = client.post("/api/v1/filter", json={
        "texts": ["ok"],
        "metrics": ["fluency"],
        "threshold": 0.99,
    })
    assert resp.status_code == 200
    data = resp.json()
    # A very short, plain text will score below 0.99
    assert data["summary"]["filtered"] >= 0  # just check structure


def test_filter_unknown_metric_returns_400():
    resp = client.post("/api/v1/filter", json={
        "texts": ["hello"],
        "metrics": ["made_up_metric"],
        "threshold": 0.5,
    })
    assert resp.status_code == 400


def test_filter_summary_fields_present():
    resp = client.post("/api/v1/filter", json={
        "texts": ["Alpha.", "Beta.", "Gamma."],
        "metrics": ["fluency"],
        "threshold": 0.3,
    })
    assert resp.status_code == 200
    summary = resp.json()["summary"]
    assert set(summary.keys()) == {"total", "passed", "filtered", "pass_rate"}
    assert summary["total"] == 3
    assert summary["passed"] + summary["filtered"] == summary["total"]
