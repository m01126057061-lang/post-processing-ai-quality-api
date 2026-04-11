"""Integration tests for POST /api/v1/feedback."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ── helpers ───────────────────────────────────────────────────────────────────

def _get_evaluation_id() -> str | None:
    """Run an evaluation and return its ID (may be None if audit disabled)."""
    resp = client.post("/api/v1/evaluate", json={
        "text": "Feedback test sentence.",
        "metrics": ["fluency"],
    })
    return resp.json().get("evaluation_id")


# ── tests ─────────────────────────────────────────────────────────────────────

def test_feedback_correct_true():
    evaluation_id = _get_evaluation_id()
    if evaluation_id is None:
        return  # audit disabled — skip
    resp = client.post("/api/v1/feedback", json={
        "evaluation_id": evaluation_id,
        "correct": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["evaluation_id"] == evaluation_id
    assert data["correct"] is True
    assert "feedback_id" in data
    assert "created_at" in data
    assert "message" in data


def test_feedback_correct_false_with_note():
    evaluation_id = _get_evaluation_id()
    if evaluation_id is None:
        return  # audit disabled — skip
    resp = client.post("/api/v1/feedback", json={
        "evaluation_id": evaluation_id,
        "correct": False,
        "note": "Score was too high for this output.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is False
    assert data["note"] == "Score was too high for this output."


def test_feedback_missing_evaluation_id_422():
    resp = client.post("/api/v1/feedback", json={"correct": True})
    assert resp.status_code == 422


def test_feedback_missing_correct_422():
    resp = client.post("/api/v1/feedback", json={"evaluation_id": "some-id"})
    assert resp.status_code == 422


def test_feedback_note_too_long_422():
    evaluation_id = _get_evaluation_id()
    if evaluation_id is None:
        return
    resp = client.post("/api/v1/feedback", json={
        "evaluation_id": evaluation_id,
        "correct": True,
        "note": "x" * 501,
    })
    assert resp.status_code == 422
