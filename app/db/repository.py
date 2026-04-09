"""
Audit trail repository — save and query evaluation records.

All database I/O is offloaded to a thread-pool executor so it does not block
the FastAPI event loop.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import sqlite3
from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.db.connection import _get_conn

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ── Sync helpers (run in executor) ──────────────────────────────────────────

def _save_sync(
    text: str,
    metrics: list[str],
    scores: dict[str, float],
    weighted_score: float,
    context_provided: bool,
) -> str:
    record_id = str(uuid4())
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO evaluations
          (id, created_at, text_hash, text_preview, metrics, scores, weighted_score, context_provided)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record_id,
            _utcnow(),
            _hash_text(text),
            text[:200],
            json.dumps(metrics),
            json.dumps(scores),
            weighted_score,
            int(context_provided),
        ),
    )
    conn.commit()
    return record_id


def _list_sync(
    limit: int,
    offset: int,
    metric: str | None,
) -> list[dict[str, Any]]:
    conn = _get_conn()
    if metric:
        rows = conn.execute(
            "SELECT * FROM evaluations WHERE metrics LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (f'%"{metric}"%', limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM evaluations ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def _count_sync(metric: str | None) -> int:
    conn = _get_conn()
    if metric:
        row = conn.execute(
            "SELECT COUNT(*) FROM evaluations WHERE metrics LIKE ?",
            (f'%"{metric}"%',),
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()
    return row[0]


# ── Async wrappers ───────────────────────────────────────────────────────────

async def save_evaluation(
    text: str,
    metrics: list[str],
    scores: dict[str, float],
    weighted_score: float,
    context_provided: bool = False,
) -> str | None:
    """Persist an evaluation record. Returns the record ID, or None if audit disabled."""
    if not settings.audit_enabled:
        return None
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, _save_sync, text, metrics, scores, weighted_score, context_provided
        )
    except sqlite3.Error as exc:
        logger.warning("Failed to save evaluation to audit DB: %s", exc)
        return None


async def list_evaluations(
    limit: int = 50,
    offset: int = 0,
    metric: str | None = None,
) -> dict[str, Any]:
    """Return paginated evaluation records with total count."""
    if not settings.audit_enabled:
        return {"total": 0, "items": [], "audit_enabled": False}
    try:
        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, _list_sync, limit, offset, metric)
        total = await loop.run_in_executor(None, _count_sync, metric)
        return {"total": total, "items": items, "audit_enabled": True}
    except sqlite3.Error as exc:
        logger.warning("Failed to list evaluations from audit DB: %s", exc)
        return {"total": 0, "items": [], "error": str(exc)}
