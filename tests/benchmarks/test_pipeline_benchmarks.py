"""Pipeline engine throughput benchmarks.

Run: pytest tests/benchmarks/ --benchmark-only
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.request import PipelineStepConfig
from app.pipeline.engine import run_pipeline

client = TestClient(app)
TEXT = "The model generates high-quality outputs most of the time."
SCORE = PipelineStepConfig(type="score", metrics=["coherence", "fluency"])
FILTER = PipelineStepConfig(type="filter", threshold=0.0)
TRANSFORM = PipelineStepConfig(type="transform", operation="strip")


@pytest.mark.benchmark(group="pipeline_engine")
def test_bench_engine_1_item(benchmark):
    benchmark(run_pipeline, [TEXT], None, [SCORE])


@pytest.mark.benchmark(group="pipeline_engine")
def test_bench_engine_10_items(benchmark):
    benchmark(run_pipeline, [TEXT] * 10, None, [SCORE, FILTER])


@pytest.mark.benchmark(group="pipeline_engine")
def test_bench_engine_50_items(benchmark):
    benchmark(run_pipeline, [TEXT] * 50, None, [SCORE, FILTER])


@pytest.mark.benchmark(group="pipeline_engine")
def test_bench_engine_100_items_all_steps(benchmark):
    benchmark(run_pipeline, [TEXT] * 100, None, [SCORE, FILTER, TRANSFORM])


@pytest.mark.benchmark(group="pipeline_http")
def test_bench_pipeline_http_10(benchmark):
    payload = {
        "texts": [TEXT] * 10,
        "steps": [
            {"type": "score", "metrics": ["coherence"]},
            {"type": "filter", "threshold": 0.0},
        ],
    }
    benchmark(lambda: client.post("/api/v1/pipeline/run", json=payload))


@pytest.mark.benchmark(group="pipeline_http")
def test_bench_pipeline_http_3_steps(benchmark):
    payload = {
        "texts": [TEXT] * 5,
        "steps": [
            {"type": "score", "metrics": ["coherence", "fluency"]},
            {"type": "filter", "threshold": 0.0},
            {"type": "transform", "operation": "strip"},
        ],
    }
    benchmark(lambda: client.post("/api/v1/pipeline/run", json=payload))
