"""
Shared embedding utilities for ML-based scorers.
The SentenceTransformer model is loaded lazily and cached — startup stays fast.
"""
from functools import lru_cache
from typing import List

import numpy as np


@lru_cache(maxsize=1)
def get_embedding_model():
    """Lazy-load and cache the sentence-transformers model."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed(texts: List[str]) -> np.ndarray:
    """Return L2-normalised embeddings for a list of strings."""
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two already-normalised vectors (simple dot product)."""
    return float(np.dot(a, b))


def norm_sim_to_score(sim: float) -> float:
    """Map cosine similarity [-1, 1] to a quality score [0, 1]."""
    return float(np.clip((sim + 1) / 2, 0.0, 1.0))
