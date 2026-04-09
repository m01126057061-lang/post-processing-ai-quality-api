"""Integration tests for POST /api/v1/pipeline/run."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_pipeline_score_and_filter():
    resp = client.post("/api/v1/pipeline/run", json={
        "texts": [
            "This is a well-formed and detailed answer to the question.",
            "bad",
        ],
        "steps": [
            {"type": "score", "metrics": ["fluency"]},
            {"type": "filter", "threshold": 0.2},
        ],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total"] == 2
    assert data["summary"]["steps_run"] == 2


def test_pipeline_transform_strip():
    resp = client.post("/api/v1/pipeline/run", json={
        "texts": ["   trimmed text   "],
        "steps": [{"type": "transform", "operation": "strip"}],
    })
    assert resp.status_code == 200
    result = resp.json()["results"][0]
    assert result["text"] == "trimmed text"


def test_pipeline_invalid_step_type_returns_400():
    resp = client.post("/api/v1/pipeline/run", json={
        "texts": ["hello"],
        "steps": [{"type": "nonexistent_step"}],
    })
    assert resp.status_code == 422  # Pydantic Literal validation fails


def test_pipeline_result_structure():
    resp = client.post("/api/v1/pipeline/run", json={
        "texts": ["Hello world."],
        "steps": [
            {"type": "score", "metrics": ["fluency"]},
        ],
    })
    assert resp.status_code == 200
    result = resp.json()["results"][0]
    assert "text" in result
    assert "scores" in result
    assert "filtered" in result
    assert "step_outputs" in result
    assert isinstance(result["step_outputs"], list)
