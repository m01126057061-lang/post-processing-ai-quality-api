"""Integration tests for POST /api/v1/filter."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
TEXTS = [
    "Machine learning is transforming industries.",
    "The sun rises in the east.",
    "Python is a popular programming language.",
]


def test_filter_200():
    assert client.post("/api/v1/filter", json={"texts": TEXTS, "threshold": 0.5}).status_code == 200


def test_filter_response_shape():
    data = client.post("/api/v1/filter", json={"texts": ["Hello."], "threshold": 0.0}).json()
    assert "results" in data
    assert "summary" in data
    s = data["summary"]
    for key in ("total", "passed", "filtered", "pass_rate"):
        assert key in s


def test_filter_all_pass_threshold_zero():
    data = client.post("/api/v1/filter", json={"texts": TEXTS, "threshold": 0.0}).json()
    assert data["summary"]["passed"] == len(TEXTS)
    assert data["summary"]["filtered"] == 0


def test_filter_total_equals_input():
    data = client.post("/api/v1/filter", json={"texts": TEXTS, "threshold": 0.5}).json()
    assert data["summary"]["total"] == len(TEXTS)


def test_filter_passed_plus_filtered_equals_total():
    data = client.post("/api/v1/filter", json={"texts": TEXTS, "threshold": 0.5}).json()
    s = data["summary"]
    assert s["passed"] + s["filtered"] == s["total"]


def test_filter_single_item():
    resp = client.post("/api/v1/filter", json={"texts": ["One sentence."], "threshold": 0.0})
    assert resp.status_code == 200
    assert resp.json()["summary"]["total"] == 1


def test_filter_results_have_required_fields():
    result = client.post("/api/v1/filter", json={"texts": ["Hello."], "threshold": 0.0}).json()["results"][0]
    assert "text" in result
    assert "filtered" in result
    assert isinstance(result["filtered"], bool)


def test_filter_pass_rate_in_range():
    pass_rate = client.post("/api/v1/filter", json={"texts": TEXTS, "threshold": 0.5}).json()["summary"]["pass_rate"]
    assert 0.0 <= pass_rate <= 1.0


def test_filter_blank_text_422():
    assert client.post("/api/v1/filter", json={"texts": ["  "], "threshold": 0.5}).status_code == 422


def test_filter_empty_texts_422():
    assert client.post("/api/v1/filter", json={"texts": [], "threshold": 0.5}).status_code == 422


def test_filter_request_id_header():
    resp = client.post("/api/v1/filter", json={"texts": ["Hello."], "threshold": 0.5})
    assert "x-request-id" in {k.lower() for k in resp.headers}
