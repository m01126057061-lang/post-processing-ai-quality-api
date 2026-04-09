"""Scorer and HTTP-level throughput benchmarks.

Run: pytest tests/benchmarks/ --benchmark-only

ML embed is mocked — these measure Python/Pydantic/dispatcher overhead.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.scorers.coherence import CoherenceScorer
from app.scorers.fluency import FluencyScorer
from app.scorers.relevance import RelevanceScorer

client = TestClient(app)
SHORT = "The quick brown fox jumps over the lazy dog."
MEDIUM = " ".join(["This is a sample AI-generated sentence."] * 10)


@pytest.mark.benchmark(group="scorers")
def test_bench_coherence(benchmark):
    benchmark(CoherenceScorer().score, MEDIUM)


@pytest.mark.benchmark(group="scorers")
def test_bench_relevance(benchmark):
    benchmark(RelevanceScorer().score, MEDIUM, SHORT)


@pytest.mark.benchmark(group="scorers")
def test_bench_fluency(benchmark):
    benchmark(FluencyScorer().score, MEDIUM)


@pytest.mark.benchmark(group="http_evaluate")
def test_bench_evaluate_single(benchmark):
    payload = {"text": MEDIUM, "metrics": ["coherence", "relevance", "fluency"]}
    benchmark(lambda: client.post("/api/v1/evaluate", json=payload))


@pytest.mark.benchmark(group="http_filter")
def test_bench_filter_10(benchmark):
    payload = {"texts": [SHORT] * 10, "threshold": 0.3, "metrics": ["coherence", "fluency"]}
    benchmark(lambda: client.post("/api/v1/filter", json=payload))


@pytest.mark.benchmark(group="http_filter")
def test_bench_filter_50(benchmark):
    payload = {"texts": [SHORT] * 50, "threshold": 0.3, "metrics": ["fluency"]}
    benchmark(lambda: client.post("/api/v1/filter", json=payload))
