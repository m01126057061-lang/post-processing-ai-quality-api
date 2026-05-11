"""
Shared embedding utilities for ML-based scorers.

The SentenceTransformer model is loaded lazily and cached — startup stays fast.
Individual text embeddings are cached with LRU (default 512 entries) to avoid
recomputing embeddings for repeated texts across batch requests.
"""
from __future__ import annotations

import os
from collections import OrderedDict
from functools import lru_cache

import numpy as np

_CACHE_SIZE = int(os.getenv("EMBEDDING_CACHE_SIZE", "512"))
_CACHE: OrderedDict[str, np.ndarray] = OrderedDict()


@lru_cache(maxsize=1)
def get_embedding_model():
    """Lazy-load and cache the sentence-transformers model (loaded once per process)."""
    from sentence_transformers import SentenceTransformer

    from app.core.config import settings
    return SentenceTransformer(settings.embedding_model)


def embed_one(text: str) -> np.ndarray:
    """Embed a single string with manual LRU cache."""
    if text in _CACHE:
        _CACHE.move_to_end(text)
        return _CACHE[text]

    model = get_embedding_model()
    result = model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
    emb = result[0]

    _CACHE[text] = emb
    _CACHE.move_to_end(text)
    if len(_CACHE) > _CACHE_SIZE:
        _CACHE.popitem(last=False)
    return emb


def embed(texts: list[str]) -> np.ndarray:
    """Return L2-normalised embeddings for a list of strings with batching and LRU cache.

    Significantly faster than sequential embed_one calls by leveraging model batching
    for all cache misses in a single request.
    """
    results = [None] * len(texts)
    missing_indices = []

    for i, text in enumerate(texts):
        if text in _CACHE:
            _CACHE.move_to_end(text)
            results[i] = _CACHE[text]
        else:
            missing_indices.append(i)

    if missing_indices:
        model = get_embedding_model()
        missing_texts = [texts[i] for i in missing_indices]
        # Batch inference for all missing texts
        embeddings = model.encode(missing_texts, convert_to_numpy=True, normalize_embeddings=True)

        for idx, emb in zip(missing_indices, embeddings, strict=True):
            results[idx] = emb
            # Update cache
            txt = texts[idx]
            _CACHE[txt] = emb
            _CACHE.move_to_end(txt)
            if len(_CACHE) > _CACHE_SIZE:
                _CACHE.popitem(last=False)

    return np.stack(results)  # type: ignore


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two already-normalised vectors (simple dot product)."""
    return float(np.dot(a, b))


def norm_sim_to_score(sim: float) -> float:
    """Map cosine similarity [-1, 1] to a quality score [0, 1]."""
    return float(np.clip((sim + 1) / 2, 0.0, 1.0))
