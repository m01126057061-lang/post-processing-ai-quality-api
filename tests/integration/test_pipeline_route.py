"""Integration tests for POST /api/v1/pipeline/run."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
TEXTS = ["The weather is nice today.", "Machine learning is complex but useful."]
SCORE = {"type": "score", "metrics": ["coherence", "fluency"]}
FILTER = {"type": "filter", "threshold": 0.0}
TRANSFORM = {"type": "transform", "operation": "strip"}


def test_pipeline_score_only_200():
    assert client.post("/api/v1/pipeline/run", json={"texts": TEXTS, "steps": [SCORE]}).status_code == 200


def test_pipeline_response_shape():
    data = client.post("/api/v1/pipeline/run", json={"texts": TEXTS, "steps": [SCORE]}).json()
    assert "results" in data and "summary" in data
    for r in data["results"]:
        assert "text" in r and "filtered" in r


def test_pipeline_score_and_filter():
    data = client.post("/api/v1/pipeline/run", json={"texts": TEXTS, "steps": [SCORE, FILTER]}).json()
    s = data["summary"]
    assert s["total"] == len(TEXTS)
    assert s["passed"] + s["filtered"] == s["total"]


def test_pipeline_three_steps():
    resp = client.post("/api/v1/pipeline/run", json={
        "texts": ["  hello  "], "steps": [SCORE, FILTER, TRANSFORM]
    })
    assert resp.status_code == 200


def test_pipeline_filter_before_score_422():
    assert client.post("/api/v1/pipeline/run", json={
        "texts": TEXTS, "steps": [FILTER, SCORE]
    }).status_code == 422


def test_pipeline_empty_steps_422():
    assert client.post("/api/v1/pipeline/run", json={"texts": TEXTS, "steps": []}).status_code == 422


def test_pipeline_blank_text_422():
    assert client.post("/api/v1/pipeline/run", json={"texts": ["  "], "steps": [SCORE]}).status_code == 422


def test_pipeline_steps_run_count():
    data = client.post("/api/v1/pipeline/run", json={"texts": TEXTS, "steps": [SCORE, FILTER]}).json()
    assert data["summary"]["steps_run"] == 2


def test_pipeline_total_equals_input():
    data = client.post("/api/v1/pipeline/run", json={"texts": TEXTS, "steps": [SCORE]}).json()
    assert data["summary"]["total"] == len(TEXTS)


def test_pipeline_transform_strips():
    data = client.post("/api/v1/pipeline/run", json={
        "texts": ["  padded  "], "steps": [{"type": "transform", "operation": "strip"}]
    }).json()
    assert data["results"][0]["text"] == "padded"


def test_pipeline_pass_rate_in_range():
    pass_rate = client.post("/api/v1/pipeline/run", json={
        "texts": TEXTS, "steps": [SCORE, FILTER]
    }).json()["summary"]["pass_rate"]
    assert 0.0 <= pass_rate <= 1.0
