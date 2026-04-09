"""
SQLite connection management and schema initialisation.

Thread-safe: uses threading.local() to give each thread its own connection.
Auto-creates the database file and schema on first call to init_db().
Disabled gracefully when AUDIT_ENABLED=false.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

_local = threading.local()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluations (
    id               TEXT    PRIMARY KEY,
    created_at       TEXT    NOT NULL,
    text_hash        TEXT    NOT NULL,
    text_preview     TEXT    NOT NULL,
    metrics          TEXT    NOT NULL,
    scores           TEXT    NOT NULL,
    weighted_score   REAL    NOT NULL,
    context_provided INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON evaluations (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evaluations_text_hash  ON evaluations (text_hash);
"""


def get_db_path() -> Path:
    return Path(settings.db_path).expanduser().resolve()


def init_db() -> None:
    """Create DB file and schema if they don't exist. Safe to call multiple times."""
    if not settings.audit_enabled:
        logger.info("Audit trail disabled (AUDIT_ENABLED=false).")
        return

    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()
    logger.info("Audit DB initialised at %s", db_path)


def _get_conn() -> sqlite3.Connection:
    """Return (or create) the thread-local DB connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(get_db_path()), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn
