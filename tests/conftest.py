"""Shared fixtures for all test modules.

``mock_embed`` (autouse) patches every embed() call so no sentence-transformer
model is loaded during the test run.
"""
import contextlib

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app

SHORT_TEXT = "The cat sat on the mat."
MEDIUM_TEXT = (
    "Machine learning is a branch of artificial intelligence. "
    "It focuses on building systems that learn from data. "
    "These systems improve their performance over time."
)
LONG_TEXT = " ".join(["This is a repeated test sentence."] * 200)


def _fake_embed(texts):
    """Return deterministic unit-vectors without loading any ML model."""
    n = len(texts)
    rng = np.random.default_rng(42)
    vecs = rng.random((n, 16)).astype(float)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms


@pytest.fixture(autouse=True)
def mock_embed(monkeypatch):
    """Patch embed() everywhere so ML models are never loaded during tests."""
    for target in (
        "app.scorers.utils.embed",
        "app.scorers.coherence.embed",
        "app.scorers.relevance.embed",
    ):
        with contextlib.suppress(AttributeError):
            monkeypatch.setattr(target, _fake_embed)
    return _fake_embed


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
