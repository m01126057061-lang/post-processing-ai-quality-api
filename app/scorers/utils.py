"""
Shared embedding utilities for ML-based scorers.

The SentenceTransformer model is loaded lazily and cached — startup stays fast.
Individual text embeddings are cached with LRU (default 512 entries) to avoid
recomputing embeddings for repeated texts across batch requests.
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

_CACHE_SIZE = int(os.getenv("EMBEDDING_CACHE_SIZE", "512"))


@lru_cache(maxsize=1)
def get_embedding_model():
    """Lazy-load and cache the sentence-transformers model (loaded once per process)."""
    from sentence_transformers import SentenceTransformer
    from app.core.config import settings
    return SentenceTransformer(settings.embedding_model)


@lru_cache(maxsize=_CACHE_SIZE)
def embed_one(text: str) -> np.ndarray:
    """Embed a single string with LRU cache.

    Cache size is controlled by the EMBEDDING_CACHE_SIZE env variable (default 512).
    This avoids redundant model inference for repeated texts in batch filter requests.
    """
    model = get_embedding_model()
    result = model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
    return result[0]


def embed(texts: list[str]) -> np.ndarray:
    """Return L2-normalised embeddings for a list of strings.

    Uses per-text LRU cache: cache hits skip model inference entirely.
    Falls back to batch encode for new texts (uses individual cached calls).
    """
    return np.stack([embed_one(t) for t in texts])


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two already-normalised vectors (simple dot product)."""
    return float(np.dot(a, b))


def norm_sim_to_score(sim: float) -> float:
    """Map cosine similarity [-1, 1] to a quality score [0, 1]."""
    return float(np.clip((sim + 1) / 2, 0.0, 1.0))
